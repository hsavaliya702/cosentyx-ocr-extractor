# Technical Flow Documentation
## Cosentyx OCR Extractor - Complete Processing Pipeline

**Document Version:** 1.0  
**Last Updated:** February 9, 2026  
**Target Audience:** Developers, Technical Architects, DevOps Engineers

---

## Table of Contents

1. [System Overview](#system-overview)
2. [OCR Processing](#ocr-processing)
3. [Information Extraction](#information-extraction)
4. [Prescription Logic](#prescription-logic)
5. [Validation Layer](#validation-layer)
6. [JSON Conversion](#json-conversion)
7. [Data Flow Diagram](#data-flow-diagram)
8. [Technical Implementation Details](#technical-implementation-details)

---

## System Overview

The Cosentyx OCR Extractor is a production-ready AWS-based pipeline that processes pharmaceutical start forms through a 5-stage workflow:

```
PDF Input → OCR → Classification → Extraction → Validation → Routing → JSON Output
```

### Core Technologies
- **AWS Textract**: OCR and form field detection
- **AWS Bedrock (Claude 3.5 Sonnet)**: Document classification and optional validation
- **Pydantic**: Data modeling and validation
- **Python 3.9+**: Core implementation language

### Processing Time
- Average: 10-30 seconds per document
- Cost: ~$0.002-$0.003 per document

---

## OCR Processing

### Stage 1: Document Input & Preprocessing

**Entry Point:** `src/processor.py` → `CosentyxFormProcessor.process_document()`

```python
def process_document(document_bytes: bytes, payload_data: Dict = None) -> ExtractionResult
```

**Input Format:**
- Raw PDF bytes
- Optional payload data (pre-filled patient information)

**PDF Conversion:**
```
PDF → Image conversion (if needed) → AWS Textract API
```

### Stage 2: AWS Textract OCR

**Location:** `src/ocr/textract_client.py`

AWS Textract extracts three types of data:

#### 2.1 Form Data (Key-Value Pairs)
```json
{
  "Patient First Name": {
    "key": "Patient First Name",
    "value": "John",
    "confidence": 0.95
  }
}
```

#### 2.2 Table Data (Structured Rows/Columns)
```json
[
  ["Product Information (Adult)", "Dosage/Quantity (28 days)", "Refills"],
  ["COSENTYX 150 mg", "Loading Dose: Inject 150 mg", "N/A"],
  ["Sensoready® Pen (1x150 mg/mL)", "on Weeks 0, 1, 2, 3", ""]
]
```

#### 2.3 Checkbox Selection Elements
```json
{
  "BlockType": "SELECTION_ELEMENT",
  "Id": "checkbox-001",
  "SelectionStatus": "SELECTED",  // or "NOT_SELECTED"
  "Confidence": 99.5,
  "Geometry": {
    "BoundingBox": {
      "Top": 0.20,
      "Left": 0.10,
      "Width": 0.02,
      "Height": 0.015
    }
  },
  "Page": 1
}
```

#### 2.4 Raw Text Blocks (LINE and WORD)
```json
{
  "BlockType": "LINE",
  "Id": "line-001",
  "Text": "Sensoready® Pen (1x150 mg/mL)",
  "Confidence": 99.0,
  "Geometry": { "BoundingBox": {...} }
}
```

### Stage 3: Textract Response Parsing

**Location:** `src/ocr/textract_parser.py`

The parser normalizes Textract's complex response into a structured format:

```python
{
  "forms": {
    "patient_first_name": {"value": "John", "confidence": 0.95},
    "patient_last_name": {"value": "Doe", "confidence": 0.98}
  },
  "tables": [
    ["Header1", "Header2"],
    ["Value1", "Value2"]
  ],
  "checkboxes": {
    "checkbox-001": True,   # SELECTED
    "checkbox-002": False   # NOT_SELECTED
  },
  "blocks": [...],  # All raw blocks for spatial analysis
  "raw_text": "Full document text..."
}
```

**Key Features:**
- Checkbox state detection (SELECTED/NOT_SELECTED)
- Table structure preservation
- Spatial coordinate tracking for proximity matching
- Confidence scores for quality assessment

---

## Information Extraction

### Stage 4: Document Classification

**Location:** `src/classification/bedrock_classifier.py`

**Purpose:** Determine document type before extraction

**Process:**
1. Send OCR text to AWS Bedrock (Claude 3.5 Sonnet)
2. LLM analyzes content and classifies as:
   - `cosentyx_start_form` (target document)
   - `ema_start_form` (alternate form type)
   - `unknown` (reject)

**Classification Prompt:**
```python
"""
Analyze this pharmaceutical form text and classify the document type.
Return JSON: {"document_type": "...", "confidence": 0.0-1.0, "reasoning": "..."}

Expected types:
- cosentyx_start_form: Cosentyx Start Form
- ema_start_form: EMA Start Form  
- unknown: Other documents
"""
```

**Output:**
```json
{
  "document_type": "cosentyx_start_form",
  "confidence": 0.99,
  "reasoning": "Document contains Cosentyx branding, prescription checkboxes..."
}
```

### Stage 5: Field Extraction (4 Extractors)

Each extractor follows the **dual-source pattern** (form + payload):

#### 5.1 Patient Extractor
**Location:** `src/extraction/patient_extractor.py`

**Fields Extracted:**
- First Name, Last Name
- Date of Birth (formatted to MM/DD/YYYY)
- Gender (M/F/Other)
- Phone (formatted to (XXX) XXX-XXXX)
- Email (validated format)
- Address (street, city, state, zip)
- Preferred Language

**Extraction Strategy:**
```python
# Step 1: Try OCR form data with fuzzy field matching
field_value, confidence = self.find_field(forms, [
    "patient first name", "first name", "fname", "given name"
])

# Step 2: Fallback to payload data if not found
if not field_value and payload_data:
    field_value = self.get_from_payload(payload_data, ["first_name", "fname"])
    confidence = 1.0
    source = "payload"

# Step 3: Validation
is_valid, formatted_value, error = FieldValidators.validate_name(field_value)

# Step 4: Create Pydantic field
return PatientField(
    value=formatted_value,
    source=source,  # "form" or "payload"
    confidence=confidence,
    validated=is_valid,
    original_value=field_value
)
```

#### 5.2 Prescriber Extractor
**Location:** `src/extraction/prescriber_extractor.py`

**Fields Extracted:**
- First Name, Last Name
- NPI (National Provider Identifier - validated 10 digits)
- Phone, Fax
- Address (street, city, state, zip)

**NPI Validation:**
```python
# Remove all non-digits
npi_digits = re.sub(r'\D', '', npi_string)

# Must be exactly 10 digits
if len(npi_digits) == 10:
    is_valid = True
    formatted = npi_digits
```

#### 5.3 Prescription Extractor (COMPLEX - Multiple Prescriptions)
**Location:** `src/extraction/prescription_extractor.py`

**THIS IS THE MOST CRITICAL COMPONENT** - See detailed section below.

#### 5.4 Attestation Extractor
**Location:** `src/extraction/attestation_extractor.py`

**Fields Extracted:**
- Signature presence (detected from Textract signature blocks)
- Signer name
- Signature date

---

## Prescription Logic

### Overview: Checkbox-Based Prescription Creation

The Cosentyx Start Form uses **checkboxes** to select prescriptions. The system creates **one prescription for each valid device + dosing combination**.

### Prescription Components

Every prescription requires:
1. **Device Selection** (Product Form): Which delivery device?
2. **Dosing Selection** (Dose Type): Which dosing schedule?
3. **Dosage** (mg amount): Determined by form section
4. **Patient Type**: Adult or Pediatric

### Form Structure

```
┌─────────────────────────────────────────────────────────────┐
│  PRODUCT INFORMATION (ADULT)                                │
├─────────────────────────────────────────────────────────────┤
│  COSENTYX 150 mg                                            │
│  ☐ Sensoready® Pen    ☐ Loading Dose: Inject 150 mg       │
│  ☐ Prefilled Syringe  ☐ Maintenance: Inject 150 mg        │
├─────────────────────────────────────────────────────────────┤
│  COSENTYX 300 mg                                            │
│  ☐ UnoReady® Pen      ☐ Loading Dose: Inject 300 mg       │
│  ☐ Sensoready® Pen    ☐ Maintenance: Inject 300 mg        │
│  ☐ Prefilled Syringe  ☐ Maintenance Increase: every 2 weeks│
├─────────────────────────────────────────────────────────────┤
│  PRODUCT INFORMATION (PEDIATRIC)                            │
├─────────────────────────────────────────────────────────────┤
│  COSENTYX 75 mg (wt <50 kg)                                │
│  ☐ Prefilled Syringe  ☐ Loading Dose: Inject 75 mg        │
│                       ☐ Maintenance: Inject 75 mg          │
├─────────────────────────────────────────────────────────────┤
│  COSENTYX 150 mg (wt ≥50 kg)                               │
│  ☐ Sensoready® Pen    ☐ Loading Dose: Inject 150 mg       │
│  ☐ Prefilled Syringe  ☐ Maintenance: Inject 150 mg        │
└─────────────────────────────────────────────────────────────┘
```

### Checkbox Detection Algorithm

**Location:** `src/extraction/prescription_extractor.py` → `_detect_from_checkboxes()`

#### Step 1: Identify All Selected Checkboxes

```python
selected_checkboxes = []
for checkbox_id, is_selected in checkboxes.items():
    if is_selected:
        selected_checkboxes.append(checkbox_id)
```

#### Step 2: Spatial Analysis - Find Nearby Text

For each selected checkbox, find associated text using **spatial proximity**:

```python
def find_nearby_text(checkbox_block, all_blocks):
    checkbox_top = checkbox_block["Geometry"]["BoundingBox"]["Top"]
    checkbox_left = checkbox_block["Geometry"]["BoundingBox"]["Left"]
    checkbox_page = checkbox_block["Page"]
    
    nearby_text = []
    for block in all_blocks:
        if block["BlockType"] != "LINE":
            continue
        if block["Page"] != checkbox_page:
            continue
        
        block_top = block["Geometry"]["BoundingBox"]["Top"]
        block_left = block["Geometry"]["BoundingBox"]["Left"]
        
        # Same row = vertical distance < 3%
        vertical_distance = abs(block_top - checkbox_top)
        if vertical_distance < 0.03:
            nearby_text.append(block["Text"])
    
    return " ".join(nearby_text)
```

#### Step 3: Classify Each Checkbox

Based on nearby text patterns:

**Device Checkboxes:**
```python
if "sensoready" in nearby_text.lower():
    checkbox_type = "device"
    form = "sensoready_pen"
elif "unoready" in nearby_text.lower():
    checkbox_type = "device"
    form = "unoready_pen"
elif "syringe" in nearby_text.lower():
    checkbox_type = "device"
    form = "syringe"
```

**Dosing Checkboxes:**
```python
if "loading dose" in nearby_text.lower():
    checkbox_type = "dosing"
    dose_type = "loading"
elif "maintenance increase" in nearby_text.lower():
    checkbox_type = "dosing"
    dose_type = "maintenance_increase"
elif "maintenance" in nearby_text.lower():
    checkbox_type = "dosing"
    dose_type = "maintenance"
```

**Dosage Detection:**
```python
# Check for dosage patterns in parentheses: (1x150mg/mL), (2x150mg/mL), etc.
if "(2x150" in nearby_text.lower():
    dosage = "300mg"  # 2 × 150mg = 300mg total
elif "75 mg" in nearby_text.lower():
    dosage = "75mg"
elif "300 mg" in nearby_text.lower():
    dosage = "300mg"
elif "150 mg" in nearby_text.lower():
    dosage = "150mg"
```

**Patient Type Detection:**
```python
# Check section headers and weight criteria
if "pediatric" in nearby_text.lower():
    patient_type = "pediatric"
elif "wt <50" in nearby_text.lower():
    patient_type = "pediatric"
elif "wt ≥50" in nearby_text.lower():
    patient_type = "pediatric"  # Pediatric ≥50kg gets 150mg
elif dosage == "75mg":
    patient_type = "pediatric"  # 75mg is always pediatric
elif dosage == "300mg":
    patient_type = "adult"  # 300mg is always adult
else:
    patient_type = "adult"  # Default
```

#### Step 4: Group Checkboxes by Section

```python
groups = {}  # Key: (patient_type, dosage)

for checkbox in classified_checkboxes:
    key = (checkbox["patient_type"], checkbox["dosage"])
    
    if key not in groups:
        groups[key] = {"devices": [], "dosings": []}
    
    if checkbox["type"] == "device":
        groups[key]["devices"].append(checkbox)
    elif checkbox["type"] == "dosing":
        groups[key]["dosings"].append(checkbox)
```

**Example Groups:**
```python
{
  ("adult", "150mg"): {
    "devices": [
      {"form": "sensoready_pen"},
      {"form": "syringe"}
    ],
    "dosings": [
      {"dose_type": "loading"},
      {"dose_type": "maintenance"}
    ]
  },
  ("adult", "300mg"): {
    "devices": [
      {"form": "unoready_pen"}
    ],
    "dosings": [
      {"dose_type": "maintenance"}
    ]
  }
}
```

#### Step 5: Create Prescriptions (Cartesian Product)

For each section, create **all combinations** of device × dosing:

```python
prescriptions = []

for (patient_type, dosage), group in groups.items():
    devices = group["devices"]
    dosings = group["dosings"]
    
    # Create prescription for each device + dosing combination
    for device in devices:
        for dosing in dosings:
            prescription = create_prescription(
                dosage=dosage,
                patient_type=patient_type,
                form=device["form"],
                dose_type=dosing["dose_type"]
            )
            prescriptions.append(prescription)
```

**Example Output:**
- Adult 150mg: 2 devices × 2 dosings = **4 prescriptions**
- Adult 300mg: 1 device × 1 dosing = **1 prescription**
- **Total: 5 prescriptions**

### Quantity Calculation

**Formula:** `quantity = doses_per_28_days × units_per_dose`

**Doses per 28 days (by dose type):**
```python
if dose_type == "loading":
    doses_per_28_days = 4  # Weeks 0, 1, 2, 3
elif dose_type == "maintenance":
    doses_per_28_days = 1  # Week 4 only (monthly)
elif dose_type == "maintenance_increase":
    doses_per_28_days = 2  # Every 2 weeks
```

**Units per dose (by device & dosage):**
```python
if dosage == "300mg":
    if form in ["sensoready_pen", "syringe"]:
        units_per_dose = 2  # (2x150mg/mL) = 2 units
    elif form == "unoready_pen":
        units_per_dose = 1  # (1x300mg/2mL) = 1 unit
else:  # 150mg or 75mg
    units_per_dose = 1  # (1x150mg/mL) or (1x75mg/mL)
```

**Examples:**
```
Adult 300mg UnoReady Pen + Loading:
  = 4 doses × 1 unit = 4

Adult 300mg Sensoready Pen + Maintenance:
  = 1 dose × 2 units = 2

Adult 300mg Prefilled Syringe + Maintenance Increase:
  = 2 doses × 2 units = 4

Adult 150mg Sensoready Pen + Loading:
  = 4 doses × 1 unit = 4
```

### Refills Extraction

**Challenge:** Refills are handwritten in blank fields on the form.

**Format:** `"12 refills, or __ refills"` where `__` is handwritten.

**Detection Strategy:**

#### 1. Table-Based Extraction (Primary)
```python
# Parse table rows to find refills column
for row in table_rows:
    row_text = " ".join(row).lower()
    
    # Match pattern: "12 refills or X"
    match = re.search(r'12\s*refills?,?\s*or\s*(\d+)', row_text)
    if match:
        handwritten_value = match.group(1)
        refills = f"12 or {handwritten_value}"
        
        # Match to prescription by row position and dose_type
        refills_by_row[row_index] = {
            "refills": refills,
            "patient_type": row_patient_type,
            "dosage": row_dosage,
            "dose_type": row_dose_type
        }
```

#### 2. Spatial Matching (Fallback)
```python
def find_refills_near_checkbox(checkbox_top, blocks):
    # Look for text blocks in the refills column (left > 0.82)
    for block in blocks:
        if block["BlockType"] == "WORD":
            block_left = block["Geometry"]["BoundingBox"]["Left"]
            block_top = block["Geometry"]["BoundingBox"]["Top"]
            
            # Same row + right column
            if block_left > 0.82 and abs(block_top - checkbox_top) < 0.02:
                text = block["Text"]
                if text.isdigit() and text != "12":
                    return f"12 or {text}"
    
    return "12 or 0"  # Default if blank
```

#### 3. Match Refills to Prescriptions
```python
for prescription in prescriptions:
    # Match by patient_type + dosage + dose_type
    for refills_entry in refills_data:
        if (refills_entry["patient_type"] == prescription.patient_type and
            refills_entry["dosage"] == prescription.dosage and
            refills_entry["dose_type"] == prescription.dose_type):
            prescription.refills.value = refills_entry["refills"]
            prescription.refills.source = "form"
            break
```

**Loading Dose Rule:**
```python
if dose_type == "loading":
    refills = "0"  # Loading doses ALWAYS have 0 refills (system rule)
```

### Prescription Object Creation

**Final Prescription Structure:**
```python
prescription = SinglePrescription(
    product=PrescriptionField(
        value="COSENTYX 300mg",
        source="form",
        confidence=0.95,
        validated=True
    ),
    dosage=PrescriptionField(
        value="300mg",
        source="form",
        confidence=0.95,
        validated=True
    ),
    form=PrescriptionField(
        value="UnoReady Pen (1x300 mg/2 mL)",
        source="form",
        confidence=0.95,
        validated=True
    ),
    dose_type=PrescriptionField(
        value="Maintenance",
        source="form",
        confidence=0.95,
        validated=True
    ),
    patient_type=PrescriptionField(
        value="Adult",
        source="form",
        confidence=0.95,
        validated=True
    ),
    quantity=PrescriptionField(
        value="1",  # Calculated: 1 dose × 1 unit
        source="lookup",
        confidence=1.0,
        validated=True
    ),
    sig=PrescriptionField(
        value="Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter",
        source="lookup",
        confidence=1.0,
        validated=True
    ),
    refills=PrescriptionField(
        value="12 or 8",  # Extracted from form
        source="form",
        confidence=1.0,
        validated=True
    )
)
```

---

## Validation Layer

### Stage 6: Field-Level Validation

**Location:** `src/validation/field_validators.py`

Each field type has a dedicated validator:

#### Name Validation
```python
def validate_name(name: str) -> Tuple[bool, str, str]:
    """
    Rules:
    - Required (not empty)
    - Only letters, spaces, hyphens, apostrophes
    - Length 2-50 characters
    """
    if not name or len(name.strip()) < 2:
        return False, name, "Name must be at least 2 characters"
    
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, name, "Name contains invalid characters"
    
    formatted = name.strip().title()
    return True, formatted, None
```

#### Date Validation
```python
def validate_date(date_str: str) -> Tuple[bool, str, str]:
    """
    Accepts: MM/DD/YYYY, M/D/YYYY, YYYY-MM-DD, etc.
    Outputs: MM/DD/YYYY (standardized format)
    """
    # Try multiple date formats
    for fmt in ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y"]:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            formatted = date_obj.strftime("%m/%d/%Y")
            return True, formatted, None
        except ValueError:
            continue
    
    return False, date_str, "Invalid date format"
```

#### Phone Validation
```python
def validate_phone(phone: str) -> Tuple[bool, str, str]:
    """
    Accepts: (123) 456-7890, 123-456-7890, 1234567890, etc.
    Outputs: (123) 456-7890 (standardized format)
    """
    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    
    # Must be exactly 10 digits
    if len(digits) == 10:
        formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return True, formatted, None
    
    return False, phone, "Phone must be 10 digits"
```

#### NPI Validation
```python
def validate_npi(npi: str) -> Tuple[bool, str, str]:
    """
    Rules:
    - Must be exactly 10 digits
    - National Provider Identifier format
    """
    digits = re.sub(r'\D', '', npi)
    
    if len(digits) == 10:
        return True, digits, None
    
    return False, npi, "NPI must be 10 digits"
```

### Stage 7: Business Rules Validation

**Location:** `src/validation/business_rules.py`

#### Duplicate Detection
```python
def check_duplicate(patient_info) -> bool:
    """
    Signature: FirstName_LastName_DOB (lowercase)
    Example: john_doe_01151980
    """
    signature = f"{first_name}_{last_name}_{dob}".lower().replace("/", "")
    
    if signature in seen_signatures:
        return True  # Duplicate found
    
    seen_signatures.add(signature)
    return False
```

#### Routing Logic
```python
def determine_routing(extraction_result) -> RoutingDecision:
    """
    Decision Tree:
    
    1. All 4 extractors valid? → create_full_profile
    2. Patient valid only? → create_patient_only
    3. Otherwise → manual_review
    """
    patient_valid = extraction_result.patient.is_valid()
    prescriber_valid = extraction_result.prescriber.is_valid()
    prescription_valid = extraction_result.prescription.is_valid()
    attestation_valid = extraction_result.attestation.is_valid()
    
    if all([patient_valid, prescriber_valid, prescription_valid, attestation_valid]):
        return RoutingDecision(
            action="create_full_profile",
            create_patient_profile=True,
            create_prescriber_profile=True,
            create_prescription=True,
            manual_review_required=False
        )
    
    elif patient_valid and not any([prescriber_valid, prescription_valid, attestation_valid]):
        return RoutingDecision(
            action="create_patient_only",
            create_patient_profile=True,
            create_prescriber_profile=False,
            create_prescription=False,
            manual_review_required=True,
            review_reason="Incomplete prescriber/prescription data"
        )
    
    else:
        return RoutingDecision(
            action="manual_review",
            create_patient_profile=False,
            create_prescriber_profile=False,
            create_prescription=False,
            manual_review_required=True,
            review_reason="Missing or invalid required fields"
        )
```

#### Prescription-Specific Rules
```python
def validate_prescription_combination(prescription) -> bool:
    """
    Business Rules:
    - Loading doses MUST have 0 refills
    - Maintenance doses MUST have refills in "12 or X" format
    - 75mg only for pediatric patients
    - 300mg only for adult patients
    """
    # Rule 1: Loading doses
    if prescription.dose_type.value == "Loading":
        if prescription.refills.value != "0":
            return False
    
    # Rule 2: 75mg restriction
    if prescription.dosage.value == "75mg":
        if prescription.patient_type.value != "Pediatric":
            return False
    
    # Rule 3: 300mg restriction
    if prescription.dosage.value == "300mg":
        if prescription.patient_type.value != "Adult":
            return False
    
    return True
```

---

## JSON Conversion

### Stage 8: Pydantic Model Serialization

**Location:** All model files inherit from `pydantic.BaseModel`

#### Pydantic Field Model
```python
from pydantic import BaseModel, Field

class PrescriptionField(BaseModel):
    value: Optional[str] = None
    source: str = "form"  # "form" or "payload" or "lookup"
    confidence: float = 0.0
    validated: bool = False
    original_value: Optional[str] = None
```

#### Prescription Model
```python
class SinglePrescription(BaseModel):
    product: PrescriptionField
    dosage: PrescriptionField
    form: PrescriptionField
    dose_type: PrescriptionField
    patient_type: PrescriptionField
    quantity: PrescriptionField
    sig: PrescriptionField
    refills: PrescriptionField
    
    def is_valid(self) -> bool:
        return all([
            self.product.validated,
            self.dosage.validated,
            self.form.validated,
            self.dose_type.validated,
            self.quantity.validated
        ])
    
    def get_display_name(self) -> str:
        return f"{self.product.value} {self.form.value} {self.dose_type.value}"
```

#### Container Models
```python
class PrescriptionInfo(BaseModel):
    prescriptions: List[SinglePrescription] = []
    
    def get_valid_prescriptions(self) -> List[SinglePrescription]:
        return [rx for rx in self.prescriptions if rx.is_valid()]
    
    def is_valid(self) -> bool:
        return len(self.get_valid_prescriptions()) > 0
```

### JSON Serialization

**Method 1: Direct Model Dump**
```python
result = processor.process_document(document_bytes)

# Convert to dictionary
result_dict = result.model_dump()

# Convert to JSON string
result_json = result.model_dump_json(indent=2)

# Save to file
with open("output.json", "w") as f:
    f.write(result_json)
```

**Method 2: Standard JSON Module**
```python
import json

result_dict = result.model_dump()
json_string = json.dumps(result_dict, indent=2)
```

### JSON Output Structure

```json
{
  "document_id": "uuid-string",
  "document_type": "cosentyx_start_form",
  "classification_confidence": 0.99,
  "extraction_timestamp": "2026-02-09T14:24:39.870431+00:00",
  "validation_status": "complete",
  
  "patient": {
    "first_name": {
      "value": "John",
      "source": "form",
      "confidence": 0.95,
      "validated": true,
      "original_value": "john"
    },
    "last_name": { "..." },
    "dob": { "..." }
  },
  
  "prescriber": {
    "first_name": { "..." },
    "npi": { "..." }
  },
  
  "prescription": {
    "prescriptions": [
      {
        "product": {
          "value": "COSENTYX 300mg",
          "source": "form",
          "confidence": 0.95,
          "validated": true,
          "original_value": null
        },
        "dosage": { "..." },
        "form": {
          "value": "UnoReady Pen (1x300 mg/2 mL)",
          "source": "form",
          "confidence": 0.95,
          "validated": true,
          "original_value": null
        },
        "dose_type": {
          "value": "Maintenance",
          "source": "form",
          "confidence": 0.95,
          "validated": true,
          "original_value": null
        },
        "quantity": {
          "value": "1",
          "source": "lookup",
          "confidence": 1.0,
          "validated": true,
          "original_value": null
        },
        "sig": {
          "value": "Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter",
          "source": "lookup",
          "confidence": 1.0,
          "validated": true,
          "original_value": null
        },
        "refills": {
          "value": "12 or 8",
          "source": "form",
          "confidence": 1.0,
          "validated": true,
          "original_value": null
        }
      }
    ]
  },
  
  "attestation": { "..." },
  
  "validation_errors": [],
  "warnings": [],
  
  "routing": {
    "action": "create_full_profile",
    "create_patient_profile": true,
    "create_prescriber_profile": true,
    "create_prescription": true,
    "manual_review_required": false,
    "review_reason": null
  },
  
  "metadata": {
    "processing_time_ms": 31592,
    "textract_cost_estimate": 0.0015,
    "bedrock_cost_estimate": 0.001
  }
}
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         PDF Document Input                       │
│                     (examples/sample_forms/*.pdf)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Step 1: AWS Textract OCR Processing                 │
│                  (src/ocr/textract_client.py)                    │
│                                                                   │
│  Input:  PDF bytes                                               │
│  Output: {                                                       │
│    forms: {"field_name": "field_value"},                         │
│    tables: [["row1_col1", "row1_col2"]],                        │
│    checkboxes: {"checkbox-id": True/False},                      │
│    blocks: [{BlockType, Text, Geometry, ...}]                   │
│  }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         Step 2: AWS Bedrock Document Classification             │
│              (src/classification/bedrock_classifier.py)          │
│                                                                   │
│  Input:  raw_text from Textract                                 │
│  LLM:    Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet)        │
│  Output: {                                                       │
│    document_type: "cosentyx_start_form",                        │
│    confidence: 0.99                                              │
│  }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Step 3: Field Extraction (4 Extractors)             │
│                    (src/extraction/*.py)                         │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  Patient         │  │  Prescriber      │                    │
│  │  Extractor       │  │  Extractor       │                    │
│  └──────────────────┘  └──────────────────┘                    │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  Prescription    │  │  Attestation     │                    │
│  │  Extractor       │  │  Extractor       │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                   │
│  Each extractor:                                                 │
│  1. Find fields using fuzzy matching                            │
│  2. Fallback to payload data if not found                       │
│  3. Apply format validators                                     │
│  4. Create Pydantic field objects                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         Step 3c: Prescription Extraction (DETAILED)              │
│           (src/extraction/prescription_extractor.py)             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 1. Detect Selected Checkboxes                          │    │
│  │    - Iterate through all SELECTION_ELEMENT blocks      │    │
│  │    - Filter: SelectionStatus == "SELECTED"             │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 2. Spatial Analysis - Find Nearby Text                 │    │
│  │    - Get checkbox position (top, left, page)           │    │
│  │    - Find LINE blocks on same page                     │    │
│  │    - Calculate vertical distance                        │    │
│  │    - Collect text within 3% vertical tolerance          │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 3. Classify Each Checkbox                              │    │
│  │    Type Detection:                                      │    │
│  │      "sensoready" → device: sensoready_pen             │    │
│  │      "unoready" → device: unoready_pen                 │    │
│  │      "syringe" → device: syringe                       │    │
│  │      "loading" → dosing: loading                       │    │
│  │      "maintenance increase" → dosing: maintenance_increase│  │
│  │      "maintenance" → dosing: maintenance               │    │
│  │                                                          │    │
│  │    Dosage Detection:                                     │    │
│  │      "(2x150" → 300mg                                    │    │
│  │      "75 mg" → 75mg                                      │    │
│  │      "150 mg" → 150mg                                    │    │
│  │                                                          │    │
│  │    Patient Type:                                         │    │
│  │      75mg → pediatric (always)                          │    │
│  │      300mg → adult (always)                             │    │
│  │      "wt <50" → pediatric                               │    │
│  │      "wt ≥50" → pediatric                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 4. Group Checkboxes by Section                         │    │
│  │    Key: (patient_type, dosage)                         │    │
│  │    Example:                                             │    │
│  │      ("adult", "150mg") → {                             │    │
│  │        devices: [sensoready_pen, syringe],             │    │
│  │        dosings: [loading, maintenance]                 │    │
│  │      }                                                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 5. Extract Refills from Tables                         │    │
│  │    - Parse table rows                                   │    │
│  │    - Match pattern: "12 refills or X"                  │    │
│  │    - Store with patient_type + dosage + dose_type      │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 6. Create Prescriptions (Cartesian Product)            │    │
│  │    For each section:                                    │    │
│  │      For each device:                                   │    │
│  │        For each dosing:                                 │    │
│  │          - Calculate quantity (doses × units)           │    │
│  │          - Lookup SIG from DOSING_INFO table            │    │
│  │          - Match refills by row position                │    │
│  │          - Create SinglePrescription object             │    │
│  │                                                          │    │
│  │    Example:                                             │    │
│  │      Adult 150mg: 2 devices × 2 dosings = 4 Rx         │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Step 4: Validation Layer (2 Levels)                 │
│                   (src/validation/*.py)                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Level 1: Field Validators                              │    │
│  │   - validate_name()                                     │    │
│  │   - validate_date()                                     │    │
│  │   - validate_phone()                                    │    │
│  │   - validate_npi()                                      │    │
│  │   - validate_email()                                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Level 2: Business Rules                                │    │
│  │   - check_duplicate()                                   │    │
│  │   - validate_prescription_combination()                │    │
│  │   - apply_routing_rules()                              │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Step 5: Routing Decision                            │
│                (src/validation/business_rules.py)                │
│                                                                   │
│  Decision Tree:                                                  │
│                                                                   │
│  All valid? ─────────YES───────→ create_full_profile            │
│      │                                                            │
│      NO                                                           │
│      │                                                            │
│      ▼                                                            │
│  Patient valid only? ─YES───────→ create_patient_only           │
│      │                                                            │
│      NO                                                           │
│      │                                                            │
│      ▼                                                            │
│  manual_review                                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│             Step 6: JSON Serialization & Output                  │
│                  (Pydantic model_dump_json())                    │
│                                                                   │
│  Output: ExtractionResult (complete JSON structure)             │
│    - document_id, document_type, classification_confidence      │
│    - patient (all fields with source, confidence, validated)    │
│    - prescriber (all fields with source, confidence, validated) │
│    - prescription.prescriptions[] (array of SinglePrescription) │
│    - attestation (signature, name, date)                        │
│    - validation_errors[], warnings[]                            │
│    - routing (action, flags, review_reason)                     │
│    - metadata (processing_time_ms, cost_estimates)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Implementation Details

### Performance Optimizations

1. **Textract Response Caching**: Parsed response stored in memory to avoid re-parsing
2. **Parallel Checkbox Classification**: All checkboxes analyzed concurrently
3. **Lazy Validation**: Only validate fields when needed for routing decisions
4. **Block Lookup Dictionary**: O(1) access to blocks by ID for spatial analysis

### Error Handling

```python
try:
    result = processor.process_document(document_bytes)
except TextractException as e:
    logger.error(f"Textract OCR failed: {str(e)}")
    # Fallback to manual review
except BedrockException as e:
    logger.error(f"Classification failed: {str(e)}")
    # Assume document type, proceed with extraction
except ValidationException as e:
    logger.error(f"Validation failed: {str(e)}")
    # Route to manual review
```

### Logging & Traceability

Every stage logs key metrics:
```python
logger.info(f"Textract OCR complete: {len(blocks)} blocks in {elapsed}ms")
logger.info(f"Classified as {doc_type} with {confidence:.1%} confidence")
logger.info(f"Extracted {len(prescriptions)} prescriptions")
logger.info(f"Validation status: {validation_status}")
logger.info(f"Routing decision: {routing_action}")
```

### Cost Tracking

```python
metadata = {
    "textract_cost_estimate": pages * 0.0015,  # $0.0015 per page
    "bedrock_cost_estimate": (input_tokens / 1000) * 0.003,  # Claude pricing
    "processing_time_ms": elapsed_time
}
```

### Scalability Considerations

- **AWS Lambda Deployment**: Scales automatically based on load
- **Stateless Processing**: Each document processed independently
- **No Database Dependencies**: Results returned as JSON for downstream processing
- **Batch Processing Support**: Can process multiple documents in parallel

---

## Appendix: Key Files Reference

| File | Purpose |
|------|---------|
| `src/processor.py` | Main orchestrator (entry point) |
| `src/ocr/textract_client.py` | AWS Textract API wrapper |
| `src/ocr/textract_parser.py` | Parse Textract response into structured format |
| `src/classification/bedrock_classifier.py` | AWS Bedrock classification |
| `src/extraction/patient_extractor.py` | Extract patient fields |
| `src/extraction/prescriber_extractor.py` | Extract prescriber fields |
| `src/extraction/prescription_extractor.py` | **Extract prescriptions (complex logic)** |
| `src/extraction/attestation_extractor.py` | Extract signature/attestation |
| `src/validation/field_validators.py` | Format validators (name, date, phone, etc.) |
| `src/validation/business_rules.py` | Business logic (routing, duplicates) |
| `src/models/*.py` | Pydantic data models |
| `src/utils/formatters.py` | Format helpers (phone, date, NPI) |

---

## Summary

The Cosentyx OCR Extractor is a sophisticated pipeline that:

1. **Receives PDF documents** and converts them to AWS Textract format
2. **Extracts structured data** using spatial analysis and pattern matching
3. **Creates multiple prescriptions** based on checkbox combinations (device × dosing)
4. **Calculates quantities** using dosing schedules and device configurations
5. **Extracts handwritten refills** from table data using regex patterns
6. **Validates all fields** using format validators and business rules
7. **Routes documents** based on data completeness and validation status
8. **Outputs JSON** with complete traceability (source, confidence, validation status)

The most complex component is the **prescription extractor**, which uses:
- Spatial proximity matching to correlate checkboxes with text
- Cartesian product logic to generate all valid device × dosing combinations
- Table parsing to extract handwritten refills values
- Lookup tables for SIG instructions and quantity calculations

The system achieves **high accuracy** by:
- Using AWS Textract's 95%+ OCR accuracy
- Applying multiple extraction strategies (checkboxes → forms → raw text)
- Validating fields at multiple levels (format → business rules)
- Tracking data source and confidence for audit trails

**End of Document**
