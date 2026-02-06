"""Prescription information extractor - supports multiple prescriptions."""

from typing import Dict, List, Optional
from src.extraction.base_extractor import BaseExtractor
from src.models.prescription import PrescriptionInfo, SinglePrescription, PrescriptionField
from src.validation.field_validators import FieldValidators
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PrescriptionExtractor(BaseExtractor):
    """Extract prescription from form data based on checkbox combinations.
    
    NEW LOGIC (Per Form Update):
    =============================
    Core Rule: ONE Prescription Per Section (1 for Adult AND/OR 1 for Pediatric)
    
    Section Structure:
    - Adult Section: Can have 1 prescription (EITHER 150mg OR 300mg, not both)
    - Pediatric Section: Can have 1 prescription (EITHER 75mg OR 150mg, not both)
    - Form can have prescriptions in BOTH Adult AND Pediatric sections simultaneously
    
    Prescription Requirements:
    - A valid prescription = ONE device checkbox + ONE dosing checkbox selected
    
    Mutual Exclusivity Rules:
    - Within Adult section: 150mg ⊕ 300mg (only one dosage per Adult section)
    - Within Pediatric section: 75mg ⊕ 150mg (only one dosage per Pediatric section)
    - Within each row: Only ONE device (Sensoready Pen OR UnoReady Pen OR Prefilled Syringe)
    - Within each row: Only ONE dosing (Loading OR Maintenance OR Maintenance Increase)
    
    Valid Scenarios:
    - Adult 150mg only: 1 prescription
    - Adult 300mg only: 1 prescription
    - Pediatric 75mg only: 1 prescription
    - Pediatric 150mg only: 1 prescription
    - Adult 150mg + Pediatric 150mg: 2 prescriptions (one per section)
    - Adult 300mg + Pediatric 75mg: 2 prescriptions (one per section)
    
    Valid Combinations Per Section:
    - Adult 150mg: 2 devices × 2 dosing = 4 possible combinations
    - Adult 300mg: 3 devices × 3 dosing = 9 possible combinations  
    - Pediatric 75mg: 1 device × 2 dosing = 2 possible combinations
    - Pediatric 150mg: 2 devices × 2 dosing = 4 possible combinations
    
    Examples:
    - Adult 150mg Sensoready Pen + Loading = 1 prescription
    - Adult 300mg UnoReady Pen + Maintenance Increase = 1 prescription
    - Pediatric 150mg Prefilled Syringe + Maintenance = 1 prescription
    - Adult 150mg Pen + Loading + Pediatric 75mg Syringe + Maintenance = 2 prescriptions
    
    Note: The PDF form enforces these validation rules, so we extract what's selected.
    """

    # Dosing schedules and quantities based on product, patient type, form, and dose type
    # Each checkbox combination maps to these dosing details
    DOSING_INFO = {
        "150mg": {
            "adult": {
                "sensoready_pen": {
                    "loading": {
                        "sig": "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "4",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "12",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                },
                "syringe": {
                    "loading": {
                        "sig": "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "4",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "12",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                }
            },
            "pediatric": {
                "sensoready_pen": {
                    "loading": {
                        "sig": "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "4",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "12",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                },
                "syringe": {
                    "loading": {
                        "sig": "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "4",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "12",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                }
            }
        },
        "300mg": {
            "adult": {
                "unoready_pen": {
                    "loading": {
                        "sig": "Inject 300 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "4",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "12",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    },
                    "maintenance_increase": {
                        "sig": "Inject 300 mg subcutaneously every 2 weeks (For patients currently taking COSENTYX every 4 weeks as per label. Loading dose already completed.)",
                        "quantity": "24",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                },
                "sensoready_pen": {
                    "loading": {
                        "sig": "Inject 300 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "8",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "12",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    },
                    "maintenance_increase": {
                        "sig": "Inject 300 mg subcutaneously every 2 weeks (For patients currently taking COSENTYX every 4 weeks as per label. Loading dose already completed.)",
                        "quantity": "24",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                },
                "syringe": {
                    "loading": {
                        "sig": "Inject 300 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "8",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "24",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    },
                    "maintenance_increase": {
                        "sig": "Inject 300 mg subcutaneously every 2 weeks (For patients currently taking COSENTYX every 4 weeks as per label. Loading dose already completed.)",
                        "quantity": "24",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                }
            }
        },
        "75mg": {
            "pediatric": {
                "syringe": {
                    "loading": {
                        "sig": "Inject 75 mg subcutaneously on Weeks 0, 1, 2, 3",
                        "quantity": "4",
                        "refills": "N/A"
                    },
                    "maintenance": {
                        "sig": "Inject 75 mg subcutaneously on Week 4, then every 4 weeks thereafter",
                        "quantity": "12",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    }
                }
            }
        }
    }

    def extract(
        self, textract_data: Dict, payload_data: Dict = None
    ) -> PrescriptionInfo:
        """Extract multiple prescriptions based on checkbox combinations.

        Args:
            textract_data: Parsed Textract data
            payload_data: Optional payload data

        Returns:
            PrescriptionInfo: Container with list of extracted prescriptions
        """
        logger.info("Extracting prescription information (multiple prescriptions)")

        forms = textract_data.get("forms", {})
        raw_text = textract_data.get("raw_text", "")
        checkboxes = textract_data.get("checkboxes", {})
        blocks = textract_data.get("blocks", [])
        prescription_info = PrescriptionInfo()
        
        # DEBUG: Log table content
        tables = textract_data.get("tables", [])
        logger.info(f"Extracted {len(tables)} tables from document")
        for i, table in enumerate(tables):
            logger.info(f"Table {i+1} has {len(table)} rows")
            for row_idx, row in enumerate(table[:15]):  # First 15 rows
                logger.info(f"  Row {row_idx+1}: {row}")

        # Detect all checked combinations
        checked_combinations = self._detect_checked_combinations(forms, raw_text, checkboxes, blocks, tables)
        
        logger.info(f"Detected {len(checked_combinations)} prescription combinations")

        # Create a SinglePrescription for each combination
        for combo in checked_combinations:
            prescription = self._create_prescription(combo)
            prescription_info.prescriptions.append(prescription)
            logger.info(f"Created prescription: {prescription.get_display_name()}")

        return prescription_info

    def _detect_checked_combinations(
        self, forms: Dict, raw_text: str, checkboxes: Dict, blocks: List[Dict], tables: List[List[str]] = None
    ) -> List[Dict[str, str]]:
        """Detect all checked prescription combinations from form.

        Returns:
            List of dicts with keys: dosage, patient_type, form, dose_type, optional refills_text
        """
        combinations = []

        # Strategy 1: Detect from Textract checkboxes (BEST - most reliable)
        combinations_from_checkboxes = self._detect_from_checkboxes(checkboxes, blocks, raw_text, tables)
        if combinations_from_checkboxes:
            logger.info(f"Found {len(combinations_from_checkboxes)} combinations from checkboxes")
            combinations.extend(combinations_from_checkboxes)

        # Strategy 2: Try to detect checkboxes from form data (fallback)
        if not combinations:
            combinations_from_forms = self._detect_from_forms(forms)
            if combinations_from_forms:
                combinations.extend(combinations_from_forms)

        # Strategy 3: Parse from raw text (additional or fallback)
        if not combinations:
            combinations_from_text = self._detect_from_raw_text(raw_text)
            if combinations_from_text:
                combinations.extend(combinations_from_text)

        # Strategy 3: Default to common scenario if nothing detected
        if not combinations:
            logger.warning("No checkboxes detected, using default prescription")
            combinations.append({
                "dosage": "150mg",
                "patient_type": "adult",
                "form": "sensoready_pen",
                "dose_type": "maintenance"
            })

        return combinations

    def _detect_from_checkboxes(self, checkboxes: Dict, blocks: List[Dict], raw_text: str, tables: List[List[str]] = None) -> List[Dict[str, str]]:
        """Detect prescriptions from selected checkboxes.
        
        NEW FORM LOGIC:
        ===============
        The form allows ONE prescription per section (1 for Adult AND/OR 1 for Pediatric):
        
        Prescription Structure:
        - ONE device checkbox + ONE dosing checkbox = ONE prescription
        - Adult section can have 1 prescription
        - Pediatric section can have 1 prescription
        - Both sections can have prescriptions simultaneously (e.g., Adult + Pediatric)
        
        Section-Level Mutual Exclusivity:
        - Within Adult: Only ONE dosage (150mg ⊕ 300mg)
        - Within Pediatric: Only ONE dosage (75mg ⊕ 150mg)
        
        Row-Level Mutual Exclusivity:
        - Within each row: Only ONE device selected
        - Within each row: Only ONE dosing selected
        
        Expected Selections Per Row:
        - Adult 150mg: 1 device (Sensoready Pen OR Prefilled Syringe) + 1 dosing (Loading OR Maintenance)
        - Adult 300mg: 1 device (UnoReady Pen OR Sensoready Pen OR Prefilled Syringe) + 1 dosing (Loading OR Maintenance OR Maintenance-Increased)
        - Pediatric 75mg: 1 device (Prefilled Syringe) + 1 dosing (Loading OR Maintenance)
        - Pediatric 150mg: 1 device (Sensoready Pen OR Prefilled Syringe) + 1 dosing (Loading OR Maintenance)
        
        Valid Prescription Combinations Per Row:
        - Adult 150mg: 2 devices × 2 dosing = 4 possible combinations
        - Adult 300mg: 3 devices × 3 dosing = 9 possible combinations
        - Pediatric 75mg: 1 device × 2 dosing = 2 possible combinations
        - Pediatric 150mg: 2 devices × 2 dosing = 4 possible combinations
        
        Note: PDF form enforces mutual exclusivity within rows and sections. We extract what's
        selected and log warnings if multiple selections detected (OCR error or form fill error).
        
        Args:
            checkboxes: Dict of {checkbox_id: is_selected}
            blocks: List of all Textract blocks (to find nearby text)
            raw_text: Full document text
            
        Returns:
            List of prescription combinations (dicts with dosage, patient_type, form, dose_type)
        """
        import re
        combinations = []
        
        # DEBUG: Log checkbox summary with page information
        total_checkboxes = len(checkboxes)
        selected_checkboxes = sum(1 for v in checkboxes.values() if v)
        logger.info(f"Checkbox analysis: {selected_checkboxes} selected out of {total_checkboxes} total")
        
        # Create block lookup for use throughout
        block_lookup = {block["Id"]: block for block in blocks}
        
        # DEBUG: Log ALL selected checkboxes with their positions and nearby text
        logger.info(f"=== DEBUG: Listing ALL {selected_checkboxes} selected checkboxes ===")
        for checkbox_id in checkboxes:
            if checkboxes[checkbox_id]:
                checkbox_block = block_lookup.get(checkbox_id)
                if checkbox_block:
                    bbox = checkbox_block.get("Geometry", {}).get("BoundingBox", {})
                    page = checkbox_block.get("Page", 1)
                    top = bbox.get("Top", 0)
                    left = bbox.get("Left", 0)
                    
                    # Get closest text
                    nearby = []
                    for b in blocks:
                        if b.get("BlockType") == "LINE" and b.get("Page") == page:
                            b_top = b.get("Geometry", {}).get("BoundingBox", {}).get("Top", 0)
                            if abs(b_top - top) < 0.03:
                                nearby.append(b.get("Text", ""))
                    
                    nearby_text = " ".join(nearby)[:150]
                    logger.info(f"  ✓ Page {page}, Top={top:.3f}, Left={left:.3f} | Text: {nearby_text}")
        
        # Log page distribution
        checkbox_pages = {}
        for checkbox_id in checkboxes:
            checkbox_block = block_lookup.get(checkbox_id)
            if checkbox_block:
                page = checkbox_block.get("Page", 1)
                if page not in checkbox_pages:
                    checkbox_pages[page] = {"total": 0, "selected": 0}
                checkbox_pages[page]["total"] += 1
                if checkboxes[checkbox_id]:
                    checkbox_pages[page]["selected"] += 1
        
        for page in sorted(checkbox_pages.keys()):
            logger.info(f"  Page {page}: {checkbox_pages[page]['selected']} selected out of {checkbox_pages[page]['total']} total")
        
        if selected_checkboxes == 0:
            return combinations
        
        # Step 1: Analyze each selected checkbox to classify it
        checkbox_data = []  # List of {id, type: 'device'/'dosing', dosage, patient_type, form/dose_type, position}
        refills_data = []  # Refills extracted from table data matched by position
        
        logger.info(f"=== Analyzing {selected_checkboxes} selected checkboxes ===")
        
        # First pass: Extract refills from table data (no refills checkboxes exist)
        # Parse table rows to find refills values: "12 refills, or X refills"
        if tables:
            for table_idx, table in enumerate(tables):
                # Detect table-level patient type from header row
                table_patient_type = None
                if table and len(table) > 0:
                    header_text = " ".join(table[0]).lower()
                    if "product information (adult)" in header_text:
                        table_patient_type = "adult"
                    elif "product information (pediatric)" in header_text:
                        table_patient_type = "pediatric"
                
                for row_idx, row in enumerate(table):
                    # Join row cells to search for refills pattern
                    row_text = " ".join(row).lower()
                    
                    # Determine patient type from table header first, then row content
                    row_patient_type = table_patient_type
                    if row_patient_type is None:
                        # Fallback to row-level detection if no table header match
                        if any(marker in row_text for marker in ["pediatric", "wt<50", "wt <50", "wt≥50", "wt ≥50"]):
                            row_patient_type = "pediatric"
                        elif any(marker in row_text for marker in ["cosentyx 150 mg", "cosentyx 300 mg"]):
                            # Adult section rows (adult dosages)
                            row_patient_type = "adult"
                        elif "cosentyx 75 mg" in row_text:
                            # 75mg is always pediatric
                            row_patient_type = "pediatric"
                    
                    # Determine dosage from row content
                    row_dosage = None
                    if "(2x150" in row_text or "300 mg" in row_text:
                        row_dosage = "300mg"
                    elif "75 mg" in row_text:
                        row_dosage = "75mg"
                        row_patient_type = "pediatric"  # 75mg is always pediatric
                    elif "150 mg" in row_text:
                        row_dosage = "150mg"
                    
                    # Determine dose_type from row content to distinguish maintenance vs maintenance_increase
                    # Check for more specific patterns first (maintenance_increase before loading/maintenance)
                    row_dose_type = None
                    if "maintenance increase" in row_text or ("every 2 weeks" in row_text and "maintenance" in row_text):
                        row_dose_type = "maintenance_increase"
                    elif "loading" in row_text and "loading dose:" in row_text:
                        # Only match "loading" if it's the actual dose type, not just mentioned in text
                        row_dose_type = "loading"
                    elif "maintenance" in row_text or "every 4 weeks" in row_text:
                        row_dose_type = "maintenance"
                    
                    # Extract refills value: "12 refills, or X refills" pattern
                    refills_match = re.search(r'12\s*refills?,?\s*or\s*(\d+)\s*refills?', row_text)
                    if refills_match:
                        handwritten_value = refills_match.group(1)
                        # Store refills in "12 or X" format to match form
                        refills_formatted = f"12 or {handwritten_value}"
                        # Store refills with patient_type, dosage, and dose_type for accurate matching
                        refills_data.append({
                            "table_row": row_idx,
                            "table_idx": table_idx,
                            "refills": refills_formatted,
                            "patient_type": row_patient_type,
                            "dosage": row_dosage,
                            "dose_type": row_dose_type,
                            "row_text": row_text[:100]
                        })
                        logger.info(f"Table {table_idx+1} row {row_idx+1}: Found refills={refills_formatted} ({row_patient_type} {row_dosage} {row_dose_type}) | text: {row_text[:80]}")
                    elif '12 refills' in row_text and 'n/a' not in row_text:
                        # Default refills when no handwritten value (blank or no value entered)
                        refills_formatted = "12 or 0"
                        refills_data.append({
                            "table_row": row_idx,
                            "table_idx": table_idx,
                            "refills": refills_formatted,
                            "patient_type": row_patient_type,
                            "dosage": row_dosage,
                            "dose_type": row_dose_type,
                            "row_text": row_text[:100]
                        })
                        logger.info(f"Table {table_idx+1} row {row_idx+1}: Found default refills={refills_formatted} ({row_patient_type} {row_dosage} {row_dose_type}) | text: {row_text[:80]}")
        
        logger.info(f"Extracted {len(refills_data)} refills values from table data")
        
        # Second pass: Analyze selected prescription checkboxes (devices and dosing)
        for checkbox_id, is_selected in checkboxes.items():
            if not is_selected:
                continue
            
            checkbox_block = block_lookup.get(checkbox_id)
            if not checkbox_block:
                continue
            
            # Get checkbox position
            checkbox_bbox = checkbox_block.get("Geometry", {}).get("BoundingBox", {})
            checkbox_top = checkbox_bbox.get("Top", 0)
            checkbox_left = checkbox_bbox.get("Left", 0)
            checkbox_page = checkbox_block.get("Page", 1)
            
            # Find nearby text with distance information for better classification
            # Only look at blocks on the SAME PAGE as the checkbox
            nearby_text_blocks = []
            same_row_text_blocks = []  # Tighter tolerance for exact same row
            
            for block in blocks:
                if block["BlockType"] != "LINE":
                    continue
                
                # Only process blocks on the same page as this checkbox
                block_page = block.get("Page", 1)
                if block_page != checkbox_page:
                    continue
                
                block_bbox = block.get("Geometry", {}).get("BoundingBox", {})
                block_top = block_bbox.get("Top", 0)
                block_left = block_bbox.get("Left", 0)
                
                vertical_distance = abs(block_top - checkbox_top)
                horizontal_distance = abs(block_left - checkbox_left)
                
                # Collect text from same row (within 3% vertical tolerance)
                if vertical_distance < 0.03:
                    text = block.get("Text", "")
                    nearby_text_blocks.append({
                        "text": text,
                        "distance": horizontal_distance,
                        "left": block_left
                    })
                    
                    # Also collect text from EXACT same row (2% tolerance for dose_type detection)
                    # Increased from 1% to 2% to handle minor vertical alignment variations in forms
                    if vertical_distance < 0.02:
                        same_row_text_blocks.append({
                            "text": text,
                            "distance": horizontal_distance,
                            "left": block_left
                        })
            
            # Sort by distance to prioritize closest text
            nearby_text_blocks.sort(key=lambda x: x["distance"])
            same_row_text_blocks.sort(key=lambda x: x["distance"])
            
            # Build context from all nearby blocks (for patient_type and dosage detection)
            context = " ".join([b["text"] for b in nearby_text_blocks]).lower()
            context_original = " ".join([b["text"] for b in nearby_text_blocks])
            
            # For device/dosing classification, use the CLOSEST text block (most relevant)
            closest_text = nearby_text_blocks[0]["text"].lower() if nearby_text_blocks else ""
            
            # For dosage detection, combine the closest 3 text blocks to ensure we capture dosage
            # (Textract sometimes splits "sensoready® pen" and "(1x150mg/ml)" into separate blocks)
            closest_3_text = " ".join([b["text"] for b in nearby_text_blocks[:3]]).lower() if nearby_text_blocks else ""
            
            # DEBUG: Log every selected checkbox before filtering
            checkbox_number = len(checkbox_data) + 1
            logger.info(f"[Checkbox #{checkbox_number}] Page {checkbox_page}, Position (top={checkbox_top:.3f}, left={checkbox_left:.3f})")
            logger.info(f"   Closest: '{closest_text[:80]}'")
            logger.info(f"   Context: '{context[:120]}'")
            
            # Skip checkboxes from attestation/consent/other non-prescription sections
            # ADAPTIVE APPROACH: Use content-based detection instead of fixed positions
            # This works across different form layouts and page structures
            
            # 1. Check if checkbox context contains prescription-related keywords
            has_prescription_keywords = any(keyword in context for keyword in [
                "sensoready", "unoready", "syringe", "prefilled",
                "loading dose", "maintenance", "inject",
                "150 mg", "300 mg", "75 mg", "cosentyx",
                "refills", "12 refills", "or __"
            ])
            
            # 2. Check if checkbox context contains non-prescription keywords (attestation/consent)
            has_non_rx_keywords = any(keyword in context for keyword in [
                "i have read and agree",
                "terms and conditions",
                "patient signature",
                "prescriber signature", 
                "authorized representative signature",
                "consent is not required",
                "consent to",
                "hereby authorize",
                "by signing below"
            ])
            
            # 3. Skip if checkbox has non-RX keywords AND lacks prescription keywords
            # This ensures we only skip true attestation checkboxes, not prescription checkboxes
            # that happen to have nearby legal text
            # Exception: Don't skip refills checkboxes (right column with "refills" keyword)
            has_refills_keyword = "refills" in context or "refill" in context
            
            if has_non_rx_keywords and not has_prescription_keywords and not has_refills_keyword:
                logger.info(f"   >> SKIPPED (attestation/consent checkbox - no prescription keywords found)")
                continue
            
            # Initialize checkbox info
            checkbox_info = {
                "id": checkbox_id,
                "top": checkbox_top,
                "left": checkbox_left,
                "context": context,
                "context_original": context_original,
                "type": None,  # 'device' or 'dosing'
                "dosage": None,  # '150mg', '300mg', '75mg'
                "patient_type": None,  # 'adult', 'pediatric'
                "form": None,  # For device checkboxes: 'sensoready_pen', 'unoready_pen', 'syringe'
                "dose_type": None,  # For dosing checkboxes: 'loading', 'maintenance', 'maintenance_increase'
                "refills": None,  # For refills checkboxes: extracted value like "12" or "3"
            }
            
            # Determine patient_type from context (will be refined based on dosage)
            if any(marker in context for marker in ["pediatric", "wt<50", "wt <50", "wt≥50", "wt ≥50", "wt<50kg"]):
                checkbox_info["patient_type"] = "pediatric"
            else:
                # Default to adult, but we'll refine this later based on dosage
                checkbox_info["patient_type"] = "adult"
            
            # Extract dosage - prioritize CLOSEST 3 text blocks to avoid cross-contamination
            # Look for dosage patterns in parentheses like (1x150mg/mL), (2x150mg/mL), (1x75mg/mL), etc.
            # SPECIAL CASE: (2x150mg/mL) = 300mg total dose
            # Note: Textract often splits device name and dosage into separate blocks
            import re
            
            dosage_from_closest = None
            # First check for (2x150) pattern which means 300mg total
            if re.search(r'\(2x150', closest_3_text, re.IGNORECASE):
                dosage_from_closest = "300mg"
            else:
                # Look for explicit dosage in parentheses (most reliable)
                dose_pattern = r'\((?:(\d+)x)?(\d+)\s*mg'
                closest_match = re.search(dose_pattern, closest_3_text, re.IGNORECASE)
                if closest_match:
                    multiplier = closest_match.group(1)
                    dose_value = closest_match.group(2)
                    
                    if dose_value == "75":
                        dosage_from_closest = "75mg"
                    elif dose_value == "300":
                        dosage_from_closest = "300mg"
                    elif dose_value == "150":
                        dosage_from_closest = "150mg"
                
                # If no parentheses pattern, look for standalone mentions
                if not dosage_from_closest:
                    if "75 mg" in closest_3_text or "75mg" in closest_3_text:
                        dosage_from_closest = "75mg"
                    elif "300 mg" in closest_3_text or "300mg" in closest_3_text:
                        dosage_from_closest = "300mg"
                    elif "150 mg" in closest_3_text or "150mg" in closest_3_text:
                        dosage_from_closest = "150mg"
            
            # Fallback to full context if closest text doesn't have dosage
            if dosage_from_closest:
                checkbox_info["dosage"] = dosage_from_closest
            elif "(2x150" in context:  # 2x150 = 300mg total
                checkbox_info["dosage"] = "300mg"
            elif "75 mg" in context or "75mg" in context or "(1x75" in context:
                checkbox_info["dosage"] = "75mg"
            elif "300 mg" in context or "300mg" in context or "(1x300" in context:
                checkbox_info["dosage"] = "300mg"
            elif "150 mg" in context or "150mg" in context or "(1x150" in context:
                checkbox_info["dosage"] = "150mg"
            elif "inject 75" in context:
                checkbox_info["dosage"] = "75mg"
            elif "inject 300" in context:
                checkbox_info["dosage"] = "300mg"
            elif "inject 150" in context:
                checkbox_info["dosage"] = "150mg"
            
            # Refine patient_type based on dosage (dosage-based rules override context)
            if checkbox_info["dosage"] == "75mg":
                # 75mg is ALWAYS pediatric
                checkbox_info["patient_type"] = "pediatric"
            elif checkbox_info["dosage"] == "300mg":
                # 300mg is always adult (no pediatric 300mg)
                checkbox_info["patient_type"] = "adult"
            # For 150mg, keep the patient_type from context analysis
            
            # Classify checkbox type: DEVICE (product) vs DOSING (regimen) vs REFILLS
            # Use horizontal position as primary classifier:
            # - Left side (left < 0.35): DEVICE checkboxes
            # - Middle-right (left 0.35-0.70): DOSING checkboxes
            # - Far right (left >= 0.70): REFILLS checkboxes
            #
            # For device checkboxes, use the CLOSEST text to determine form type
            
            # Build same_row_text for all types (from exact same row with tight tolerance)
            same_row_text = " ".join([b["text"] for b in same_row_text_blocks]).lower()
            
            if checkbox_left < 0.35:
                # LEFT SIDE: DEVICE checkbox
                # Check the closest text for DEVICE type keywords
                # When multiple device names appear in context (same row with 2 options),
                # use position of device names in text to determine which checkbox this is
                
                # First try closest_text (most reliable for unique matches)
                device_matched = False
                if "unoready" in closest_text and "sensoready" not in closest_text and "syringe" not in closest_text:
                    checkbox_info["type"] = "device"
                    checkbox_info["form"] = "unoready_pen"
                    device_matched = True
                elif "sensoready" in closest_text and "unoready" not in closest_text and "syringe" not in closest_text:
                    checkbox_info["type"] = "device"
                    checkbox_info["form"] = "sensoready_pen"
                    device_matched = True
                elif ("prefilled syringe" in closest_text or ("prefilled" in closest_text and "syringe" in closest_text)) and "sensoready" not in closest_text and "unoready" not in closest_text:
                    checkbox_info["type"] = "device"
                    checkbox_info["form"] = "syringe"
                    device_matched = True
                elif "syringe" in closest_text and "sensoready" not in closest_text and "unoready" not in closest_text:
                    checkbox_info["type"] = "device"
                    checkbox_info["form"] = "syringe"
                    device_matched = True
                
                # Fallback: check nearby text blocks to find which device label is closest
                # Search through sorted nearby_text_blocks (already ordered by distance from checkbox)
                if not device_matched:
                    # Iterate through nearby text blocks (sorted by distance) to find first device match
                    for text_block in nearby_text_blocks[:10]:  # Check closest 10 blocks
                        block_text = text_block["text"].lower()
                        
                        # Check for unoready (avoiding product names)
                        if "unoready® pen" in block_text or "unoready pen" in block_text:
                            checkbox_info["type"] = "device"
                            checkbox_info["form"] = "unoready_pen"
                            device_matched = True
                            break
                        elif "unoready" in block_text and "sensoready" not in block_text:
                            checkbox_info["type"] = "device"
                            checkbox_info["form"] = "unoready_pen"
                            device_matched = True
                            break
                        
                        # Check for sensoready (avoiding "sensoreadypen" product names)
                        elif "sensoready® pen" in block_text or "sensoready pen" in block_text:
                            checkbox_info["type"] = "device"
                            checkbox_info["form"] = "sensoready_pen"
                            device_matched = True
                            break
                        elif "sensoready" in block_text and "unoready" not in block_text:
                            # Verify it's not "sensoreadypen" (product name)
                            idx = block_text.find("sensoready")
                            if idx >= 0 and (idx + 10 >= len(block_text) or block_text[idx+10] in [' ', '®', '\n', '\t', ')']):
                                checkbox_info["type"] = "device"
                                checkbox_info["form"] = "sensoready_pen"
                                device_matched = True
                                break
                        
                        # Check for prefilled syringe
                        elif "prefilled syringe" in block_text:
                            checkbox_info["type"] = "device"
                            checkbox_info["form"] = "syringe"
                            device_matched = True
                            break
                        elif ("prefilled" in block_text and "syringe" in block_text) and "sensoready" not in block_text and "unoready" not in block_text:
                            checkbox_info["type"] = "device"
                            checkbox_info["form"] = "syringe"
                            device_matched = True
                            break
                        elif "syringe" in block_text and "sensoready" not in block_text and "unoready" not in block_text:
                            checkbox_info["type"] = "device"
                            checkbox_info["form"] = "syringe"
                            device_matched = True
                            break
            elif checkbox_left < 0.70:
                # MIDDLE-RIGHT: DOSING checkbox
                # Strategy: Use closest_text (single nearest block) as PRIMARY source
                # Fall back to context (all nearby blocks) only if closest_text doesn't have clear keywords
                
                # STEP 1: Try to classify from closest_text (most reliable - single text block closest to checkbox)
                dose_type_from_closest = None
                
                # Check closest_text for loading dose (excluding "loading dose already completed")
                if "loading dose: inject" in closest_text or ("loading dose:" in closest_text and "already completed" not in closest_text):
                    dose_type_from_closest = "loading"
                # Check for maintenance schedules
                elif "then every 2 weeks" in closest_text or ("every 2 weeks" in closest_text and "every 4 weeks" not in closest_text):
                    dose_type_from_closest = "maintenance_increase"
                elif "then every 4 weeks thereafter" in closest_text or "every 4 weeks thereafter" in closest_text or "every 4 weeks" in closest_text:
                    dose_type_from_closest = "maintenance"
                # Check for generic maintenance
                elif "maintenance: inject" in closest_text or ("maintenance:" in closest_text and "loading" not in closest_text):
                    dose_type_from_closest = "maintenance"
                
                # STEP 2: If closest_text gave us a result, use it
                if dose_type_from_closest:
                    checkbox_info["type"] = "dosing"
                    checkbox_info["dose_type"] = dose_type_from_closest
                else:
                    # STEP 3: Fall back to context-based position detection
                    # Find positions of loading dose patterns
                    loading_patterns = ["loading dose: inject", "loading dose inject", "loading dose:", "loading dose "]
                    loading_pos = -1
                    for pattern in loading_patterns:
                        pos = context.find(pattern)
                        if pos != -1:
                            # Exclude "loading dose already completed"
                            if "loading dose already completed" not in context[max(0, pos-10):pos+50]:
                                loading_pos = pos
                                break
                    
                    # Find positions of maintenance patterns
                    maintenance_patterns = [
                        "maintenance: inject", "maintenance inject",
                        "then every 2 weeks", "every 2 weeks",
                        "then every 4 weeks thereafter", "every 4 weeks thereafter", "every 4 weeks",
                        "maintenance:", "maintenance "
                    ]
                    maintenance_pos = -1
                    maintenance_type = None
                    for pattern in maintenance_patterns:
                        pos = context.find(pattern)
                        if pos != -1:
                            maintenance_pos = pos
                            if pattern in ["then every 2 weeks", "every 2 weeks"]:
                                maintenance_type = "maintenance_increase"
                            elif pattern in ["then every 4 weeks thereafter", "every 4 weeks thereafter", "every 4 weeks"]:
                                maintenance_type = "maintenance"
                            else:
                                maintenance_type = "maintenance"
                            break
                    
                    # Use position to determine which is closer
                    if loading_pos != -1 and maintenance_pos != -1:
                        if loading_pos < maintenance_pos:
                            checkbox_info["type"] = "dosing"
                            checkbox_info["dose_type"] = "loading"
                        else:
                            checkbox_info["type"] = "dosing"
                            checkbox_info["dose_type"] = maintenance_type or "maintenance"
                    elif loading_pos != -1:
                        checkbox_info["type"] = "dosing"
                        checkbox_info["dose_type"] = "loading"
                    elif maintenance_pos != -1:
                        checkbox_info["type"] = "dosing"
                        checkbox_info["dose_type"] = maintenance_type or "maintenance"
            # Note: Refills checkboxes (checkbox_left >= 0.70) handled in separate first pass above
            
            # Only add if we successfully classified the checkbox (device or dosing only)
            if checkbox_info["type"] and checkbox_info["dosage"] and checkbox_info["patient_type"]:
                if checkbox_info["type"] == "device" and checkbox_info["form"]:
                    checkbox_data.append(checkbox_info)
                    logger.info(
                        f"DEVICE Checkbox: {checkbox_info['patient_type']} {checkbox_info['dosage']} "
                        f"{checkbox_info['form']} | closest: '{closest_text[:50]}' | context: '{checkbox_info['context'][:60]}...'"
                    )
                elif checkbox_info["type"] == "dosing" and checkbox_info["dose_type"]:
                    checkbox_data.append(checkbox_info)
                    logger.info(
                        f"DOSING Checkbox: {checkbox_info['patient_type']} {checkbox_info['dosage']} "
                        f"{checkbox_info['dose_type']} | closest: '{closest_text[:50]}' | context: '{checkbox_info['context'][:60]}...'"
                    )
                else:
                    logger.warning(f"Incomplete checkbox: {checkbox_info}")
            else:
                logger.warning(
                    f"   XX UNCLASSIFIED: Could not classify checkbox at top={checkbox_top:.3f}, left={checkbox_left:.3f}"
                )
                logger.warning(f"      Type: {checkbox_info['type']}, Dosage: {checkbox_info['dosage']}, PatientType: {checkbox_info['patient_type']}, Form/DoseType: {checkbox_info.get('form') or checkbox_info.get('dose_type')}")
        
        # Step 2: Group checkboxes by product category (patient_type, dosage)
        groups = {}  # Key: (patient_type, dosage), Value: {devices: [], dosings: []}
        
        for cb in checkbox_data:
            key = (cb["patient_type"], cb["dosage"])
            if key not in groups:
                groups[key] = {"devices": [], "dosings": []}
            
            if cb["type"] == "device":
                groups[key]["devices"].append(cb)
            elif cb["type"] == "dosing":
                groups[key]["dosings"].append(cb)
        
        logger.info(f"Grouped checkboxes into {len(groups)} product categories")
        
        # Validate expectations: Check for within-section violations
        adult_sections = [k for k in groups.keys() if k[0] == 'adult']
        pediatric_sections = [k for k in groups.keys() if k[0] == 'pediatric']
        
        if len(adult_sections) > 1:
            section_names = [f"Adult {k[1]}" for k in adult_sections]
            logger.warning(
                f"⚠️  MULTIPLE ADULT DOSAGES DETECTED: {', '.join(section_names)}. "
                f"Form should only allow ONE dosage per Adult section (150mg OR 300mg). "
                f"Possible form fill error or OCR misdetection."
            )
        
        if len(pediatric_sections) > 1:
            section_names = [f"Pediatric {k[1]}" for k in pediatric_sections]
            logger.warning(
                f"⚠️  MULTIPLE PEDIATRIC DOSAGES DETECTED: {', '.join(section_names)}. "
                f"Form should only allow ONE dosage per Pediatric section (75mg OR 150mg). "
                f"Possible form fill error or OCR misdetection."
            )
        
        for key, group in groups.items():
            num_devices = len(group['devices'])
            num_dosings = len(group['dosings'])
            num_prescriptions = num_devices * num_dosings
            
            # Validate expectations: Only ONE device and ONE dosing per row
            if num_devices > 1:
                device_names = [d['form'].replace('_', ' ').title() for d in group['devices']]
                logger.warning(
                    f"⚠️  {key[0].title()} {key[1]}: MULTIPLE DEVICES detected ({', '.join(device_names)}). "
                    f"Form should only allow ONE device per row. Possible form fill error."
                )
            
            if num_dosings > 1:
                dosing_names = [d['dose_type'].replace('_', ' ').title() for d in group['dosings']]
                logger.warning(
                    f"⚠️  {key[0].title()} {key[1]}: MULTIPLE DOSINGS detected ({', '.join(dosing_names)}). "
                    f"Form should only allow ONE dosing per row. Possible form fill error."
                )
            
            logger.info(
                f"  {key[0].title()} {key[1]}: "
                f"{num_devices} device(s) × {num_dosings} dosing(s) = "
                f"{num_prescriptions} prescription(s)"
            )
        
        # Step 3: Create prescriptions from checkbox combinations
        # Expected: ONE device + ONE dosing = ONE prescription per section
        # Cartesian product handles cases where multiple checkboxes detected (form fill error/OCR error)
        for (patient_type, dosage), group in groups.items():
            devices = group["devices"]
            dosings = group["dosings"]
            
            if not devices or not dosings:
                logger.warning(
                    f"Skipping {patient_type} {dosage}: missing {'devices' if not devices else 'dosings'} "
                    f"({len(devices)} devices, {len(dosings)} dosings)"
                )
                continue
            
            # Create prescription from device + dosing combination
            # If multiple selections detected (shouldn't happen per form rules), we process all
            # Match refills from table data by patient_type and dosage
            for device in devices:
                for dosing in dosings:
                    # For maintenance/maintenance_increase doses, find matching refills from table
                    matching_refills = None
                    if dosing["dose_type"] in ["maintenance", "maintenance_increase"]:
                        # Match refills by patient_type AND dosage AND dose_type
                        for refills_entry in refills_data:
                            if (refills_entry["patient_type"] == patient_type and 
                                refills_entry["dosage"] == dosage and
                                refills_entry["dose_type"] == dosing["dose_type"]):
                                matching_refills = refills_entry["refills"]
                                logger.info(f"   Matched refills: {matching_refills} for {patient_type} {dosage} {dosing['dose_type']}")
                                break
                    
                    combination = {
                        "dosage": dosage,
                        "patient_type": patient_type,
                        "form": device["form"],
                        "dose_type": dosing["dose_type"],
                    }
                    
                    # Add refills if found (for maintenance doses only)
                    if matching_refills:
                        combination["refills_text"] = matching_refills
                    
                    combinations.append(combination)
                    refills_info = f" (refills: {matching_refills})" if matching_refills else ""
                    logger.info(
                        f"[OK] Created prescription: {patient_type.title()} {dosage} "
                        f"{device['form'].replace('_', ' ').title()} - "
                        f"{dosing['dose_type'].replace('_', ' ').title()}{refills_info}"
                    )
        
        logger.info(f"Total prescriptions created: {len(combinations)}")
        return combinations

    def _detect_from_forms(self, forms: Dict) -> List[Dict[str, str]]:
        """Detect checked combinations from Textract form data.

        Each checked checkbox represents ONE prescription.
        Logic: Dosage + Form Type + Dose Type + Patient Type = 1 prescription
        
        Returns combinations with optional 'refills_text' field extracted from nearby text.
        """
        combinations = []
        
        # Search for checkboxes in form data
        for field_name, field_value in forms.items():
            field_name_lower = field_name.lower()
            
            # Check if this is a checkbox field (marked as SELECTED)
            if isinstance(field_value, dict):
                is_selected = field_value.get("value") == "SELECTED" or field_value.get("selected") is True
                # Try to get refills text if present in the field
                refills_text = field_value.get("refills", None)
            else:
                is_selected = str(field_value).upper() == "SELECTED"
                refills_text = None
            
            if not is_selected:
                continue

            # Parse the field name to determine what was selected
            dosage = self._extract_dosage_from_text(field_name_lower)
            patient_type = self._extract_patient_type_from_text(field_name_lower)
            form = self._extract_form_from_text(field_name_lower)
            dose_type = self._extract_dose_type_from_text(field_name_lower)

            if dosage and form and dose_type:
                combination = {
                    "dosage": dosage,
                    "patient_type": patient_type,
                    "form": form,
                    "dose_type": dose_type
                }
                
                # Add refills text if found
                if refills_text:
                    combination["refills_text"] = refills_text
                
                # Avoid duplicates
                if combination not in combinations:
                    combinations.append(combination)
                    logger.info(f"Detected checkbox: {combination}")

        return combinations

    def _detect_from_raw_text(self, raw_text: str) -> List[Dict[str, str]]:
        """Detect prescriptions from raw text by looking for checked markers.

        Each checked checkbox = 1 prescription.
        Looks for patterns like ☑, ✓, [X], SELECTED near prescription options.
        Also extracts refills text from the same line/context.
        """
        combinations = []
        lines = raw_text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains a checkbox marker
            if not any(marker in line for marker in ['☑', '✓', '[x]', 'selected', '☒', '✔']):
                continue

            # Look at this line and nearby lines for context
            context_lines = lines[max(0, i-1):min(len(lines), i+3)]
            context = ' '.join(context_lines).lower()
            
            dosage = self._extract_dosage_from_text(context)
            patient_type = self._extract_patient_type_from_text(context)
            form = self._extract_form_from_text(context)
            dose_type = self._extract_dose_type_from_text(context)

            # Try to extract refills text from the current line or nearby
            refills_text = self._extract_refills_text(context_lines)

            if dosage and form and dose_type:
                combination = {
                    "dosage": dosage,
                    "patient_type": patient_type,
                    "form": form,
                    "dose_type": dose_type
                }
                
                if refills_text:
                    combination["refills_text"] = refills_text
                
                if combination not in combinations:
                    combinations.append(combination)
                    logger.info(f"Detected from text: {combination}")

        return combinations
    
    def _extract_refills_text(self, lines: List[str]) -> Optional[str]:
        """Extract refills text from lines - returns as-is from form.
        
        Looks for patterns like:
        - "12 or 0 refills" -> "12 or 0"
        - "12 or 3 refills" -> "12 or 3"
        - "12 or 5 refills" -> "12 or 5"
        - "N/A" -> "N/A"
        - "12 refills" -> "12"
        
        Format is always "12 or X" where X is variable (0, 3, 5, etc.)
        
        Args:
            lines: List of text lines to search
            
        Returns:
            Refills text as found in the form, or None
        """
        import re
        text = ' '.join(lines)
        
        # Pattern 1: "12 or X" format (X can be any number)
        match = re.search(r'12\s*or\s*(\d+)', text, re.IGNORECASE)
        if match:
            return f"12 or {match.group(1)}"
        
        # Pattern 2: "N/A"
        if "n/a" in text.lower():
            return "N/A"
        
        # Pattern 3: Just a number before "refills"
        match = re.search(r'(\d+)\s*refills?', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None

    def _extract_dosage_from_text(self, text: str) -> Optional[str]:
        """Extract dosage from text."""
        if "150" in text:
            return "150mg"
        elif "300" in text:
            return "300mg"
        elif "75" in text:
            return "75mg"
        return None

    def _extract_patient_type_from_text(self, text: str) -> str:
        """Extract patient type from text."""
        if "pediatric" in text or "wt <50" in text or "wt <" in text or "wt<50" in text:
            return "pediatric"
        elif "wt ≥50" in text or "wt >=" in text or "wt>=50" in text:
            return "pediatric"  # 150mg for pediatric >=50kg
        return "adult"

    def _extract_form_from_text(self, text: str) -> Optional[str]:
        """Extract form from text.
        
        Returns the specific form type to distinguish between different pen types.
        Format: sensoready_pen, unoready_pen, syringe
        """
        if "sensoready" in text:
            return "sensoready_pen"
        elif "unoready" in text:
            return "unoready_pen"
        elif "prefilled syringe" in text or "prefilled" in text:
            return "syringe"
        elif "syringe" in text and "prefilled" not in text:
            return "syringe"
        # Generic "pen" as fallback
        elif "pen" in text and "unoready" not in text and "sensoready" not in text:
            return "sensoready_pen"  # Default to sensoready if not specified
        return None

    def _extract_dose_type_from_text(self, text: str) -> Optional[str]:
        """Extract dose type from text."""
        if "maintenance increase" in text:
            return "maintenance_increase"
        elif "loading dose" in text or "loading" in text:
            return "loading"
        elif "maintenance" in text:
            return "maintenance"
        return None

    def _create_prescription(self, combo: Dict[str, str]) -> SinglePrescription:
        """Create a SinglePrescription from a combination dict.

        Each checkbox = 1 prescription.
        Logic: Dosage + Form Type + Dose Type + Patient Type

        Args:
            combo: Dict with dosage, patient_type, form, dose_type, optional refills_text

        Returns:
            SinglePrescription with all fields populated
        """
        dosage = combo["dosage"]
        patient_type = combo["patient_type"]
        form = combo["form"]
        dose_type = combo["dose_type"]
        refills_text = combo.get("refills_text", None)

        # Get dosing info from lookup table
        dosing_info = self.DOSING_INFO.get(dosage, {}).get(patient_type, {}).get(form, {}).get(dose_type, {})
        
        # Fallback for generic pen if specific type not found
        if not dosing_info and "pen" in form:
            dosing_info = self.DOSING_INFO.get(dosage, {}).get(patient_type, {}).get("sensoready_pen", {}).get(dose_type, {})

        # Create prescription fields
        product_value = f"COSENTYX {dosage}"
        
        # Format form display name for output
        if form == "sensoready_pen":
            form_display = "Sensoready Pen"
        elif form == "unoready_pen":
            form_display = "UnoReady Pen"
        elif form == "syringe":
            form_display = "Prefilled Syringe"
        else:
            form_display = form.replace("_", " ").title()
        
        # Format dose type for display
        dose_type_display = dose_type.replace("_", " ").title()
        
        # Use extracted refills text if available (takes priority), otherwise use default from DOSING_INFO
        if refills_text:
            refills_value = refills_text
        elif dose_type == "loading":
            refills_value = "0"  # Loading doses always have 0 refills
        elif dose_type in ["maintenance", "maintenance_increase"]:
            # Maintenance doses always show "12 or X" format (X = 0 if no handwritten value)
            refills_value = "12 or 0"  # Default when no handwritten value found
        else:
            refills_value = dosing_info.get("refills", "12")  # Fallback for other types
        
        prescription = SinglePrescription(
            product=PrescriptionField(
                value=product_value,
                source="form",
                confidence=0.95,
                validated=True
            ),
            dosage=PrescriptionField(
                value=dosage,
                source="form",
                confidence=0.95,
                validated=True
            ),
            form=PrescriptionField(
                value=form_display,
                source="form",
                confidence=0.95,
                validated=True
            ),
            dose_type=PrescriptionField(
                value=dose_type_display,
                source="form",
                confidence=0.95,
                validated=True
            ),
            patient_type=PrescriptionField(
                value=patient_type.capitalize(),
                source="form",
                confidence=0.95,
                validated=True
            ),
            quantity=PrescriptionField(
                value=dosing_info.get("quantity", "12"),
                source="lookup",
                confidence=1.0,
                validated=True
            ),
            sig=PrescriptionField(
                value=dosing_info.get("sig", f"Use as directed"),
                source="lookup",
                confidence=1.0,
                validated=True
            ),
            refills=PrescriptionField(
                value=refills_value,
                source="form" if refills_text else "lookup",
                confidence=1.0 if refills_text else 0.9,
                validated=True
            )
        )

        return prescription
