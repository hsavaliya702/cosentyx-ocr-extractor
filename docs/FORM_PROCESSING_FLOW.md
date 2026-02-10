# Cosentyx Start Form Processing Flow

This document explains how the Cosentyx/EMA Start Form is processed through the complete pipeline, from PDF upload to final JSON output with routing decisions.

---

## Overview: Complete Pipeline

```
┌─────────────────┐
│   PDF Input     │  4-page Cosentyx Start Form (241 KB)
└────────┬────────┘
         ▼
┌─────────────────┐
│      OCR        │  AWS Textract extracts ~3,071 blocks
│  (AWS Textract) │  • 421 LINE blocks (text)
└────────┬────────┘  • 2,433 WORD blocks (individual words + handwritten)
         │           • 53 SELECTION_ELEMENT blocks (checkboxes)
         │           • 4 TABLE blocks (prescription tables)
         ▼           • 156 CELL blocks (table cells)
┌─────────────────┐
│ Classification  │  AWS Bedrock (Claude 3.5 Sonnet)
│ (AWS Bedrock)   │  → Determines: "cosentyx_start_form"
└────────┬────────┘  → Confidence: 98%
         ▼
┌─────────────────┐
│   Extraction    │  4 Specialized Extractors parse OCR data
│                 │  ├─ PatientExtractor
│                 │  ├─ PrescriberExtractor
│                 │  ├─ PrescriptionExtractor ← COMPLEX LOGIC
│                 │  └─ AttestationExtractor
└────────┬────────┘
         ▼
┌─────────────────┐
│   Validation    │  Multi-level validation
│                 │  ├─ Field validators (format, NPI, date)
│                 │  ├─ Business rules (completeness)
│                 │  └─ Optional: Bedrock semantic validation
└────────┬────────┘
         ▼
┌─────────────────┐
│    Routing      │  Decision: create_full_profile / create_patient_only / manual_review
│                 │  Based on: which extractors passed validation
└────────┬────────┘
         ▼
┌─────────────────┐
│  JSON Output    │  Structured data with metadata, confidence scores, routing action
└─────────────────┘
```

**Processing Time:** 10-30 seconds  
**Cost:** ~$0.0025 per document ($0.0015 Textract + $0.0010 Bedrock)

---

## Form Structure: Prescription Section

The Cosentyx Start Form contains prescription checkboxes organized in a grid pattern:

### Adult Section (Page 3)

```
┌──────────────────────┬───────────────────────────────┬─────────────────┐
│ Product Information  │ Dosage/Quantity (28 days)     │ Refills         │
├──────────────────────┼───────────────────────────────┼─────────────────┤
│ COSENTYX 150 mg      │ ☑ Loading Dose: Inject 150 mg│ N/A             │
│ ☑ Sensoready® Pen    │   on Weeks 0,1,2,3            │                 │
│ ☐ Prefilled Syringe  │ ☑ Maintenance: Inject 150 mg  │ 12 refills,     │
│   (1x150 mg/mL)      │   on Week 4, then every 4     │ or __12__ refills│
│                      │   weeks thereafter             │                 │
├──────────────────────┼───────────────────────────────┼─────────────────┤
│ COSENTYX 300 mg      │ ☐ Loading Dose: Inject 300 mg│ N/A             │
│ ☐ UnoReady® Pen      │   on Weeks 0,1,2,3            │                 │
│ ☐ Sensoready® Pen    │ ☐ Maintenance: Inject 300 mg  │ 12 refills,     │
│ ☐ Prefilled Syringe  │   on Week 4, then every 4     │ or _____ refills│
│   (2x150 mg/mL)      │   weeks thereafter             │                 │
│                      │ ☑ Maintenance Increase (HS):  │ 12 refills,     │
│                      │   Inject 300 mg every 2 weeks │ or __5__ refills │
└──────────────────────┴───────────────────────────────┴─────────────────┘
```

### Pediatric Section (Page 3)

```
┌──────────────────────┬───────────────────────────────┬─────────────────┐
│ Product Information  │ Dosage/Quantity (28 days)     │ Refills         │
├──────────────────────┼───────────────────────────────┼─────────────────┤
│ COSENTYX 75 mg       │ ☑ Loading Dose: Inject 75 mg │ N/A             │
│ (wt <50 kg)          │   on Weeks 0,1,2,3            │                 │
│ ☑ Prefilled Syringe  │ ☐ Maintenance: Inject 75 mg   │ 12 refills,     │
│   (1x75 mg/mL)       │   on Week 4, then every 4     │ or _____ refills│
│                      │   weeks thereafter             │                 │
├──────────────────────┼───────────────────────────────┼─────────────────┤
│ COSENTYX 150 mg      │ ☐ Loading Dose: Inject 150 mg│ N/A             │
│ (wt ≥50 kg)          │   on Weeks 0,1,2,3            │                 │
│ ☐ Sensoready® Pen    │ ☐ Maintenance: Inject 150 mg  │ 12 refills,     │
│ ☐ Prefilled Syringe  │   on Week 4, then every 4     │ or _____ refills│
│   (1x150 mg/mL)      │   weeks thereafter             │                 │
└──────────────────────┴───────────────────────────────┴─────────────────┘
```

**Key Observations:**
- **2 columns of checkboxes**: Left = Device type, Middle = Dosing schedule
- **1 prescription = 1 device + 1 dosing** (Cartesian product)
- **Refills column**: "12 refills, or __X__ refills" with handwritten values (X = 3, 5, 7, 12, etc.)
- **Multiple sections**: Adult 150mg, Adult 300mg, Pediatric 75mg, Pediatric 150mg

---

## Step-by-Step Processing

### STEP 1: PDF Input

**Input:** 4-page PDF (CosentyxStartForm-8.pdf, 241 KB)

**Pre-Processing:**
```python
# Convert PDF to PNG images (one per page)
PDFConverter.convert_all_pages_to_images(pdf_bytes)
# → [Page1.png, Page2.png, Page3.png, Page4.png]
```

**Output:** 4 PNG images
- Page 1: 752.5 KB (patient/insurance info)
- Page 2: 372.2 KB (clinical info)
- Page 3: 862.6 KB (prescription grid) ← MOST IMPORTANT
- Page 4: 1,094.7 KB (attestation/signatures)

---

### STEP 2: OCR with AWS Textract

**API Call:** `analyze_document()` with `FeatureTypes: ["FORMS", "TABLES", "SIGNATURES"]`

**Processing:**
```python
for page_num, page_bytes in enumerate(pages, 1):
    response = textract.analyze_document(page_bytes)
    # API returns JSON with "Blocks" array
    
# Merge all pages into single dataset
```

**Textract Response Structure (JSON):**
```json
{
  "Blocks": [
    {
      "BlockType": "SELECTION_ELEMENT",
      "SelectionStatus": "SELECTED",
      "Confidence": 99.1,
      "Geometry": {
        "BoundingBox": {
          "Top": 0.309,    // Position on page (0.0-1.0)
          "Left": 0.184,   // Position on page (0.0-1.0)
          "Width": 0.016,
          "Height": 0.012
        }
      },
      "Id": "checkbox-uuid",
      "Page": 3
    },
    {
      "BlockType": "WORD",
      "Text": "12",
      "TextType": "PRINTED",
      "Confidence": 99.5,
      "Geometry": {
        "BoundingBox": {
          "Top": 0.310,
          "Left": 0.805
        }
      },
      "Page": 3
    },
    {
      "BlockType": "WORD",
      "Text": "3",            // Handwritten refills value
      "TextType": "HANDWRITING",
      "Confidence": 95.2,
      "Geometry": {
        "BoundingBox": {
          "Top": 0.311,
          "Left": 0.850   // Right column (refills area)
        }
      },
      "Page": 3
    },
    {
      "BlockType": "LINE",
      "Text": "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter",
      "Confidence": 98.7,
      "Geometry": { /* ... */ },
      "Page": 3
    },
    {
      "BlockType": "CELL",
      "RowIndex": 3,
      "ColumnIndex": 3,
      "Text": "12 refills, or refills",  // Table cell (missing handwritten value)
      "Relationships": [
        {"Type": "CHILD", "Ids": ["word-id-1", "word-id-2"]}
      ]
    }
  ]
}
```

**Extracted Data from Page 3:**
- **754 blocks** from Page 1
- **296 blocks** from Page 2
- **798 blocks** from Page 3 (prescriptions)
- **1,223 blocks** from Page 4
- **Total: 3,071 blocks**

**Block Breakdown:**
- `WORD` blocks: 2,433 (individual words, including handwritten digits)
- `LINE` blocks: 421 (full text lines)
- `SELECTION_ELEMENT` blocks: 53 (checkboxes)
  - 6 SELECTED
  - 47 NOT_SELECTED
- `TABLE` blocks: 4 (prescription tables)
- `CELL` blocks: 156 (table cells)

**Parsed Structure:**
```python
textract_data = {
    "forms": {
        "patient first name": "yachna",
        "date of birth": "08/09/1967",
        # ... 23 key-value pairs
    },
    "tables": [
        # Table 1: Insurance info (3 rows)
        # Table 2: Patient/Prescriber info (6 rows)
        # Table 3: Adult prescriptions (6 rows)
        [
            ["Product Information (Adult)", "Dosage/Quantity (28 days)", "Refills Rx"],
            ["COSENTYX 150 mg", "Loading Dose: Inject 150 mg...", "N/A"],
            ["Sensoready® Pen...", "Maintenance: Inject 150 mg...", "12 refills, or refills"],
            # Note: Handwritten values NOT in table cells
        ],
        # Table 4: Pediatric prescriptions (5 rows)
    ],
    "checkboxes": {
        "checkbox-id-1": True,   // Sensoready Pen (150mg)
        "checkbox-id-2": True,   // Loading (150mg)
        "checkbox-id-3": True,   // Maintenance (150mg)
        "checkbox-id-4": False,  // UnoReady Pen (300mg)
        # ... 53 total checkboxes
    },
    "blocks": [ /* all 3,071 raw blocks for spatial analysis */ ],
    "raw_text": "Sign up online at www.covermymeds.health..."
}
```

**Key Challenge:** Handwritten refills values (3, 5, 7) appear as separate WORD blocks, NOT inside table cells!

---

### STEP 3: Classification with AWS Bedrock

**API Call:** Bedrock Runtime (`invoke_model`) with Claude 3.5 Sonnet

**Input to LLM:**
```json
{
  "prompt": "Classify this document based on the following text:\n\n[First 3000 chars of raw_text]...",
  "options": [
    "ema_start_form",
    "cosentyx_start_form", 
    "other"
  ]
}
```

**LLM Response:**
```json
{
  "document_type": "cosentyx_start_form",
  "confidence": 0.98,
  "reasoning": "Document contains 'COSENTYX' branding, prescription grid with dosing schedules..."
}
```

**Result:**
- Document Type: `cosentyx_start_form`
- Confidence: 98%
- Processing Time: ~2 seconds
- Cost: ~$0.001

---

### STEP 4: Extraction (4 Specialized Extractors)

#### 4a. Patient Extraction
**Input:** `forms`, `raw_text`, `payload_data`

**Logic:**
```python
# Try fuzzy matching in forms data
first_name = find_field(forms, ["patient first name", "first name", "fname"])
last_name = find_field(forms, ["patient last name", "last name", "lname"])
dob = find_field(forms, ["date of birth", "dob", "birth date"])

# Fallback to payload data if not found
if not first_name and payload_data:
    first_name = payload_data.get("first_name")
```

**Output:**
```python
PatientInfo(
    first_name=PatientField(value="yachna", source="form", confidence=0.9, validated=False),
    last_name=PatientField(value="*", source="form", confidence=0.9, validated=False),
    date_of_birth=PatientField(value="*", source="form", validated=False),
    # ... other fields
    valid=False  # Missing required fields or validation failed
)
```

#### 4b. Prescriber Extraction
**Similar to patient extraction** - extracts NPI, name, address, phone, fax

**Output:**
```python
PrescriberInfo(
    npi=PrescriberField(value="345678901", validated=False),
    # ... other fields
    valid=False
)
```

#### 4c. Prescription Extraction ← **MOST COMPLEX**

**Input:** `textract_data.blocks`, `textract_data.tables`

##### **Algorithm: Checkbox-Based Detection**

```python
def extract_prescriptions(blocks, tables):
    # PHASE 1: Extract refills from table text (placeholder values)
    refills_data = []
    for table in tables:
        for row in table:
            row_text = " ".join(row).lower()
            # Pattern: "12 refills, or X refills"
            match = re.search(r'12\s*refills?,?\s*or\s*(\d+)\s*refills?', row_text)
            if match:
                refills_data.append({
                    "patient_type": detect_patient_type(row_text),  # adult/pediatric
                    "dosage": detect_dosage(row_text),              # 150mg/300mg/75mg
                    "dose_type": detect_dose_type(row_text),        # loading/maintenance
                    "refills": f"12 or {match.group(1)}"
                })
    
    # PHASE 2: Analyze selected checkboxes
    checkbox_data = []
    for block in blocks:
        if block["BlockType"] != "SELECTION_ELEMENT":
            continue
        if block["SelectionStatus"] != "SELECTED":
            continue
        
        # Get checkbox position
        bbox = block["Geometry"]["BoundingBox"]
        checkbox_top = bbox["Top"]
        checkbox_left = bbox["Left"]
        
        # Find nearby text blocks (within 0.03 vertical distance)
        nearby_text = find_nearby_text(blocks, checkbox_top, checkbox_left)
        context = " ".join(nearby_text).lower()
        
        # Classify checkbox type based on nearby text
        if is_device_checkbox(context):
            # LEFT COLUMN: Device type (Sensoready Pen, Prefilled Syringe, etc.)
            checkbox_data.append({
                "type": "device",
                "form": detect_form_type(context),  # "sensoready_pen", "syringe"
                "dosage": detect_dosage(context),   # "150mg", "300mg", "75mg"
                "patient_type": detect_patient_type(context)  # "adult", "pediatric"
            })
        elif is_dosing_checkbox(context):
            # MIDDLE COLUMN: Dosing schedule (Loading, Maintenance, etc.)
            checkbox_data.append({
                "type": "dosing",
                "dose_type": detect_dose_type(context),  # "loading", "maintenance"
                "dosage": detect_dosage(context),
                "patient_type": detect_patient_type(context)
            })
            
            # SPATIAL SEARCH: Find handwritten refills in right column
            if dose_type in ["maintenance", "maintenance_increase"]:
                refills = find_refills_near_checkbox(blocks, checkbox_top, checkbox_left)
                # Search for WORD blocks: left > 0.70, same row (top ± 0.035)
                # Skip "12" (default), extract digits like "3", "5", "7"
    
    # PHASE 3: Group by section (patient_type + dosage)
    groups = {
        ("adult", "150mg"): {"devices": [], "dosings": []},
        ("adult", "300mg"): {"devices": [], "dosings": []},
        ("pediatric", "75mg"): {"devices": [], "dosings": []},
        ("pediatric", "150mg"): {"devices": [], "dosings": []}
    }
    
    for checkbox in checkbox_data:
        key = (checkbox["patient_type"], checkbox["dosage"])
        if checkbox["type"] == "device":
            groups[key]["devices"].append(checkbox)
        elif checkbox["type"] == "dosing":
            groups[key]["dosings"].append(checkbox)
    
    # PHASE 4: Create prescriptions via Cartesian product
    prescriptions = []
    for (patient_type, dosage), group in groups.items():
        devices = group["devices"]
        dosings = group["dosings"]
        
        # 1 device × 1 dosing = 1 prescription
        for device in devices:
            for dosing in dosings:
                # Match refills by patient_type + dosage + dose_type
                matching_refills = None
                for refills_entry in refills_data:
                    if (refills_entry["patient_type"] == patient_type and
                        refills_entry["dosage"] == dosage and
                        refills_entry["dose_type"] == dosing["dose_type"]):
                        matching_refills = refills_entry["refills"]
                        break
                
                prescription = create_prescription(
                    dosage=dosage,
                    patient_type=patient_type,
                    form=device["form"],
                    dose_type=dosing["dose_type"],
                    refills=matching_refills or dosing.get("refills")
                )
                prescriptions.append(prescription)
    
    return prescriptions
```

##### **Example: Adult 150mg Section**

**Selected Checkboxes:**
1. ☑ Sensoready® Pen (left column, device)
2. ☑ Loading Dose (middle column, dosing)
3. ☑ Maintenance (middle column, dosing)

**Spatial Analysis:**
```python
# Checkbox 1: "Sensoready® Pen"
position = (top=0.309, left=0.184)  # LEFT column
nearby_text = ["prefilled syringe", "(1x150 mg/ml)", "sensoready® pen", "cosentyx 150 mg"]
→ Classified as: DEVICE checkbox (adult 150mg, sensoready_pen)

# Checkbox 2: "Loading Dose"
position = (top=0.290, left=0.435)  # MIDDLE column
nearby_text = ["loading dose: inject 150 mg subcutaneously on weeks o, 1, 2, 3"]
→ Classified as: DOSING checkbox (adult 150mg, loading)

# Checkbox 3: "Maintenance"
position = (top=0.309, left=0.435)  # MIDDLE column
nearby_text = ["maintenance: inject 150 mg subcutaneously on week 4, then every 4 weeks"]
# Spatial refills search: Find WORD blocks at (top ≈ 0.309, left > 0.70)
#   Found: "12" at (0.310, 0.805) → SKIP (default value)
#   Found: "12" at (0.311, 0.850) → KEEP (handwritten value)
→ Classified as: DOSING checkbox (adult 150mg, maintenance, refills="12 or 12")
```

**Cartesian Product:**
```
devices = [sensoready_pen]
dosings = [loading, maintenance]

Combinations:
1. sensoready_pen × loading = Prescription #1
2. sensoready_pen × maintenance = Prescription #2
```

**Created Prescriptions:**
```python
[
    SinglePrescription(
        product="COSENTYX 150mg",
        dosage="150mg",
        form="Sensoready Pen (1x150 mg/mL)",
        dose_type="Loading",
        patient_type="Adult",
        quantity="4",        # Formula: 4 doses × 1 unit = 4
        refills="0",         # Loading doses have 0 refills
        sig="Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3"
    ),
    SinglePrescription(
        product="COSENTYX 150mg",
        dosage="150mg",
        form="Sensoready Pen (1x150 mg/mL)",
        dose_type="Maintenance",
        patient_type="Adult",
        quantity="1",        # Formula: 1 dose × 1 unit = 1
        refills="12 or 12",  # Extracted from spatial search
        sig="Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter"
    )
]
```

**Complete Output:**
```python
PrescriptionInfo(
    prescriptions=[
        # Adult 150mg: 1 device × 2 dosings = 2 prescriptions
        SinglePrescription(...),  # Sensoready Pen + Loading
        SinglePrescription(...),  # Sensoready Pen + Maintenance
        
        # Pediatric 75mg: 1 device × 1 dosing = 1 prescription
        SinglePrescription(...)   # Prefilled Syringe + Loading
    ],
    total_prescriptions=3,
    valid=True  # At least 1 prescription extracted
)
```

#### 4d. Attestation Extraction
**Extracts signature blocks and date**

**Output:**
```python
AttestationInfo(
    signature_present=False,
    prescriber_name="*",
    date=None,
    valid=False
)
```

---

### STEP 5: Validation

#### Field Validators
```python
# Date validation
FieldValidators.validate_date("08/09/1967")
→ (True, "08/09/1967", None)

# NPI validation
FieldValidators.validate_npi("345678901")
→ (True, "3456789012", None)  # Must be 10 digits

# Phone validation
FieldValidators.validate_phone("(555) 123-4567")
→ (True, "5551234567", None)
```

#### Business Rules
```python
BusinessRules.apply_routing_rules(extraction_result)

Logic:
- IF patient.valid AND prescriber.valid AND prescription.valid AND attestation.valid:
    → routing_action = "create_full_profile"
- ELIF patient.valid AND (prescriber invalid OR prescription invalid OR attestation invalid):
    → routing_action = "create_patient_only"
- ELSE:
    → routing_action = "manual_review"
```

**Result:**
```python
routing_action = "manual_review"
routing_reason = "Missing or invalid patient information"
```

---

### STEP 6: Routing Decision

**Logic Tree:**
```
┌─ All 4 extractors valid? ─ YES → create_full_profile
│                           │       (Create patient, prescriber, prescriptions, attestation)
│                           │
│                           NO
│                           │
└─ Patient valid only? ──── YES → create_patient_only
                            │       (Create patient record, queue others for manual review)
                            │
                            NO
                            │
                            → manual_review
                              (Send entire form to manual review queue)
```

**For This Document:**
- Patient: ❌ Invalid (missing/incorrect DOB, name)
- Prescriber: ❌ Invalid (NPI format incorrect)
- Prescription: ✅ Valid (3 prescriptions extracted)
- Attestation: ❌ Invalid (no signature)

**Decision:** `manual_review` (patient and prescriber need manual review)

---

### STEP 7: JSON Output

**Complete Output Structure:**
```json
{
  "document_id": "ff54f335-9a1c-4acf-b5d0-ca9ed19e3e1b",
  "metadata": {
    "document_type": "cosentyx_start_form",
    "classification_confidence": 0.98,
    "processing_time_ms": 32952,
    "timestamp": "2026-02-09T20:46:01Z",
    "costs": {
      "textract": 0.0015,
      "bedrock": 0.0010,
      "total": 0.0025
    }
  },
  "patient": {
    "first_name": {
      "value": "yachna",
      "source": "form",
      "confidence": 0.9,
      "validated": false,
      "original_value": "yachna"
    },
    "last_name": {
      "value": "*",
      "source": "form",
      "confidence": 0.9,
      "validated": false
    },
    "date_of_birth": {
      "value": "*",
      "source": "form",
      "validated": false
    },
    "valid": false
  },
  "prescriber": {
    "npi": {
      "value": "345678901",
      "source": "form",
      "confidence": 0.9,
      "validated": false
    },
    "valid": false
  },
  "prescription": {
    "prescriptions": [
      {
        "product": {
          "value": "COSENTYX 150mg",
          "source": "form",
          "confidence": 0.95,
          "validated": true
        },
        "dosage": {
          "value": "150mg",
          "source": "form",
          "confidence": 0.95,
          "validated": true
        },
        "form": {
          "value": "Sensoready Pen (1x150 mg/mL)",
          "source": "form",
          "confidence": 0.95,
          "validated": true
        },
        "dose_type": {
          "value": "Maintenance",
          "source": "form",
          "confidence": 0.95,
          "validated": true
        },
        "patient_type": {
          "value": "Adult",
          "source": "form",
          "confidence": 0.95,
          "validated": true
        },
        "quantity": {
          "value": "1",
          "source": "lookup",
          "confidence": 1.0,
          "validated": true
        },
        "refills": {
          "value": "12 or 12",
          "source": "form",
          "confidence": 0.95,
          "validated": true
        },
        "sig": {
          "value": "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter",
          "source": "lookup",
          "confidence": 1.0,
          "validated": true
        },
        "valid": true
      },
      {
        "product": {"value": "COSENTYX 150mg", "...": "..."},
        "dose_type": {"value": "Loading", "...": "..."},
        "quantity": {"value": "4", "...": "..."},
        "refills": {"value": "0", "...": "..."},
        "valid": true
      },
      {
        "product": {"value": "COSENTYX 75mg", "...": "..."},
        "dose_type": {"value": "Loading", "...": "..."},
        "patient_type": {"value": "Pediatric", "...": "..."},
        "valid": true
      }
    ],
    "total_prescriptions": 3,
    "valid": true
  },
  "attestation": {
    "signature_present": false,
    "valid": false
  },
  "validation": {
    "overall_status": "failed",
    "patient_valid": false,
    "prescriber_valid": false,
    "prescription_valid": true,
    "attestation_valid": false
  },
  "routing": {
    "action": "manual_review",
    "create_patient_profile": false,
    "create_prescriber_profile": false,
    "create_prescriptions": false,
    "manual_review_required": true,
    "reason": "Missing or invalid patient information"
  }
}
```

**Key Features:**
- ✅ **Complete traceability**: Every field includes source, confidence, validation status
- ✅ **Routing decision**: Clear action based on validation results
- ✅ **Cost tracking**: Itemized AWS service costs
- ✅ **Processing metadata**: Timing, classification confidence
- ✅ **Structured prescriptions**: Each prescription fully detailed with all fields

---

## Technical Deep Dive: Prescription Extraction

### Challenge: Handwritten Refills Values

**Problem:** Textract table parsing returns `"12 refills, or refills"` but the handwritten value (3, 5, 7) is missing!

**Why?** Textract extracts:
1. **Table CELL blocks** → Text in cells (includes printed "12 refills, or refills")
2. **Separate WORD blocks** → Handwritten digits appear as independent blocks OUTSIDE table structure

**Solution:** Spatial proximity search

```python
def find_refills_near_checkbox(blocks, checkbox_top, checkbox_left):
    """Find handwritten refills value spatially near a checkbox."""
    for block in blocks:
        if block["BlockType"] != "WORD":
            continue
        
        bbox = block["Geometry"]["BoundingBox"]
        block_top = bbox["Top"]
        block_left = bbox["Left"]
        
        # Refills column: left > 0.70 (right side of form)
        if block_left < 0.70:
            continue
        
        # Same row: vertical distance < 0.035
        if abs(block_top - checkbox_top) > 0.035:
            continue
        
        text = block["Text"]
        
        # Skip "12" (default printed value)
        if text == "12":
            continue
        
        # Found handwritten digit!
        if text.isdigit():
            return f"12 or {text}"
    
    return None
```

**Example:**
```
Checkbox at (top=0.309, left=0.435) → Maintenance dose

Search WORD blocks:
  - Block: "12" at (0.310, 0.805) → SKIP (default value)
  - Block: "12" at (0.311, 0.850) → FOUND (handwritten)
  
Result: "12 or 12"
```

### Quantity Calculation Formula

```python
quantity = doses_per_28_days × units_per_dose

Examples:
- Loading 150mg Sensoready Pen:
  doses_per_28_days = 4 (weeks 0,1,2,3)
  units_per_dose = 1 (single 150mg pen)
  → quantity = 4 × 1 = 4

- Maintenance 300mg Prefilled Syringe:
  doses_per_28_days = 1 (every 4 weeks)
  units_per_dose = 2 (two 150mg syringes = 300mg)
  → quantity = 1 × 2 = 2

- Maintenance Increase 300mg:
  doses_per_28_days = 2 (every 2 weeks)
  units_per_dose = 2 (two 150mg units)
  → quantity = 2 × 2 = 4
```

---

## Performance & Costs

### Timing Breakdown
| Stage | Time | Percentage |
|-------|------|------------|
| PDF Conversion | 8s | 24% |
| Textract OCR (4 pages) | 20s | 61% |
| Bedrock Classification | 2s | 6% |
| Extraction | 1s | 3% |
| Validation | <1s | <1% |
| **Total** | **33s** | **100%** |

### Cost Breakdown
| Service | Cost | Notes |
|---------|------|-------|
| Textract | $0.0015 | $1.50/1000 pages × 4 pages = $0.006 ÷ 4 |
| Bedrock | $0.0010 | ~300 input tokens + 50 output tokens |
| **Total** | **$0.0025** | Per document |

**At Scale:**
- 1,000 documents/month = $2.50
- 10,000 documents/month = $25.00
- 100,000 documents/month = $250.00

---

## Error Handling & Edge Cases

### Common Issues

1. **Missing Handwritten Values**
   - **Symptom:** Refills show "12 or 0" instead of actual value
   - **Cause:** Handwritten digit positioned outside search tolerance
   - **Fix:** Increase vertical tolerance from 0.035 to 0.05

2. **Multiple Devices Selected**
   - **Symptom:** 2 devices × 1 dosing = 2 prescriptions
   - **Cause:** Form error (should only check one device)
   - **Behavior:** System processes all combinations (Cartesian product)

3. **Low OCR Confidence**
   - **Symptom:** Confidence < 85% on handwritten text
   - **Behavior:** Still extracted but flagged for manual review
   - **Threshold:** Configurable via `TEXTRACT_CONFIDENCE_THRESHOLD`

4. **PDF Conversion Failures**
   - **Symptom:** Poppler not installed or corrupted PDF
   - **Fallback:** Error result with manual_review routing

---

## Configuration

### Environment Variables

```ini
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Textract
TEXTRACT_CONFIDENCE_THRESHOLD=0.85  # Minimum OCR confidence
TEXTRACT_MAX_RETRIES=3

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_TEMPERATURE=0.1  # Deterministic classification

# Validation
ENABLE_DUPLICATE_CHECK=true
ENABLE_BEDROCK_VALIDATION=false  # Optional semantic validation

# Debug
DEBUG_MODE=false  # Enable detailed Textract block logging
LOG_LEVEL=INFO
```

---

## Summary

**Input:** 4-page Cosentyx Start Form PDF (241 KB)

**Process:**
1. ✅ Convert PDF to 4 PNG images
2. ✅ OCR with Textract → 3,071 blocks (checkboxes, text, tables)
3. ✅ Classify with Bedrock → "cosentyx_start_form" (98% confidence)
4. ✅ Extract via 4 extractors → Patient, Prescriber, Prescriptions (3), Attestation
5. ✅ Validate fields → Check formats, business rules
6. ✅ Route based on validation → manual_review (patient/prescriber invalid)
7. ✅ Generate JSON → Complete structured output with metadata

**Output:** JSON with 3 valid prescriptions + routing action

**Performance:** 33 seconds, $0.0025

**Key Innovation:** Spatial proximity matching for handwritten refills extraction from checkbox-based prescription grid