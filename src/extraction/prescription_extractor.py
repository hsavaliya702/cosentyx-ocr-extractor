"""Prescription information extractor - supports multiple prescriptions."""

from typing import Dict, List, Optional
from src.extraction.base_extractor import BaseExtractor
from src.models.prescription import PrescriptionInfo, SinglePrescription, PrescriptionField
from src.validation.field_validators import FieldValidators
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PrescriptionExtractor(BaseExtractor):
    """Extract prescription from form data based on checkbox combinations.
    
    CURRENT LOGIC:
    ==============
    Create prescriptions for ANY selected device/dosing combinations.

    Prescription Requirements:
    - A valid prescription = ONE device checkbox + ONE dosing checkbox selected

    Combinations Per Section (if all selected):
    - Adult 150mg: 2 devices × 2 dosing = 4 possible combinations
    - Adult 300mg: 3 devices × 3 dosing = 9 possible combinations
    - Pediatric 75mg: 1 device × 2 dosing = 2 possible combinations
    - Pediatric 150mg: 2 devices × 2 dosing = 4 possible combinations

    Examples:
    - Adult 150mg Sensoready Pen + Loading = 1 prescription
    - Adult 300mg UnoReady Pen + Maintenance Increase = 1 prescription
    - Pediatric 150mg Prefilled Syringe + Maintenance = 1 prescription
    - Adult 150mg Pen + Loading + Pediatric 75mg Syringe + Maintenance = 2 prescriptions

    Note: We do not enforce one-prescription-per-section; we output all selected combinations.
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
                        "quantity": "1",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    },
                    "maintenance_increase": {
                        "sig": "Inject 300 mg subcutaneously every 2 weeks (For patients currently taking COSENTYX every 4 weeks as per label. Loading dose already completed.)",
                        "quantity": "2",
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
                        "quantity": "2",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    },
                    "maintenance_increase": {
                        "sig": "Inject 300 mg subcutaneously every 2 weeks (For patients currently taking COSENTYX every 4 weeks as per label. Loading dose already completed.)",
                        "quantity": "4",
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
                        "quantity": "2",
                        "refills": "12 or 0"  # Default, will be extracted from form
                    },
                    "maintenance_increase": {
                        "sig": "Inject 300 mg subcutaneously every 2 weeks (For patients currently taking COSENTYX every 4 weeks as per label. Loading dose already completed.)",
                        "quantity": "4",
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
        
        CURRENT LOGIC:
        ===============
        Create prescriptions for any selected device/dosing combinations.

        Prescription Structure:
        - ONE device checkbox + ONE dosing checkbox = ONE prescription

        Expected Selections Per Row:
        - Adult 150mg: devices (Sensoready Pen OR Prefilled Syringe) + dosing (Loading OR Maintenance)
        - Adult 300mg: devices (UnoReady Pen OR Sensoready Pen OR Prefilled Syringe) + dosing (Loading OR Maintenance OR Maintenance-Increased)
        - Pediatric 75mg: device (Prefilled Syringe) + dosing (Loading OR Maintenance)
        - Pediatric 150mg: devices (Sensoready Pen OR Prefilled Syringe) + dosing (Loading OR Maintenance)

        Valid Prescription Combinations Per Row:
        - Adult 150mg: 2 devices × 2 dosing = 4 possible combinations
        - Adult 300mg: 3 devices × 3 dosing = 9 possible combinations
        - Pediatric 75mg: 1 device × 2 dosing = 2 possible combinations
        - Pediatric 150mg: 2 devices × 2 dosing = 4 possible combinations
        
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
                        # We see the generic pattern \"12 refills, or ___ refills\" but Textract
                        # has not captured any handwritten override (no digit after \"or\").
                        # To avoid incorrectly assuming a value (e.g., 0) when handwriting might
                        # be present but unreadable, treat the second value as unknown here.
                        refills_formatted = "12 or Unknown"
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

        # Build section headers and product row anchors to improve page/row matching
        section_headers = []  # List of {page, top, patient_type}
        product_rows = []  # List of {page, top, dosage, patient_type}
        for block in blocks:
            if block.get("BlockType") != "LINE":
                continue
            text = block.get("Text", "")
            if not text:
                continue
            text_lower = text.lower()
            page = block.get("Page", 1)
            bbox = block.get("Geometry", {}).get("BoundingBox", {})
            top = bbox.get("Top", 0)

            if "product information (adult)" in text_lower:
                section_headers.append({"page": page, "top": top, "patient_type": "adult"})
            elif "product information (pediatric)" in text_lower:
                section_headers.append({"page": page, "top": top, "patient_type": "pediatric"})

            if "cosentyx" in text_lower and ("150 mg" in text_lower or "300 mg" in text_lower or "75 mg" in text_lower):
                dosage = None
                if "300 mg" in text_lower:
                    dosage = "300mg"
                elif "150 mg" in text_lower:
                    dosage = "150mg"
                elif "75 mg" in text_lower:
                    dosage = "75mg"

                patient_type = None
                if "pediatric" in text_lower or "wt<50" in text_lower or "wt <50" in text_lower or "wt≥50" in text_lower or "wt ≥50" in text_lower:
                    patient_type = "pediatric"
                elif dosage == "75mg":
                    patient_type = "pediatric"
                elif dosage == "300mg":
                    patient_type = "adult"

                product_rows.append(
                    {"page": page, "top": top, "dosage": dosage, "patient_type": patient_type, "text": text_lower}
                )
        
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
                combined_distance = horizontal_distance + (vertical_distance * 2.0)
                
                # Collect text from same row (within 3% vertical tolerance)
                if vertical_distance < 0.03:
                    text = block.get("Text", "")
                    nearby_text_blocks.append({
                        "text": text,
                        "distance": combined_distance,
                        "left": block_left
                    })
                    
                    # Also collect text from EXACT same row (2% tolerance for dose_type detection)
                    # Increased from 1% to 2% to handle minor vertical alignment variations in forms
                    if vertical_distance < 0.02:
                        same_row_text_blocks.append({
                            "text": text,
                            "distance": combined_distance,
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

            def _find_refills_near_checkbox(page, top, blocks_for_page):
                import re
                refills_lines = []
                for blk in blocks_for_page:
                    if blk.get("BlockType") != "LINE":
                        continue
                    if blk.get("Page", 1) != page:
                        continue
                    text = blk.get("Text", "")
                    if not text:
                        continue
                    text_lower = text.lower()
                    if "refills" not in text_lower:
                        continue
                    bbox = blk.get("Geometry", {}).get("BoundingBox", {})
                    blk_left = bbox.get("Left", 0)
                    if blk_left < 0.70:
                        continue
                    blk_top = bbox.get("Top", 0)
                    refills_lines.append((blk_top, blk_left, text_lower))

                candidates = []
                for line_top, line_left, line_text in refills_lines:
                    if abs(line_top - top) > 0.06:
                        continue
                    match = re.search(r'12\s*refills?,?\s*or\s*(\d+)', line_text)
                    if match and match.group(1) != "12":
                        candidates.append((match.group(1), line_top, line_left, True))
                        continue
                    match = re.search(r'\bor\s*(\d+)\b', line_text)
                    if match and match.group(1) != "12":
                        candidates.append((match.group(1), line_top, line_left, True))
                        continue
                    match = re.search(r'(\d+)\s*refills?', line_text)
                    if match and match.group(1) != "12":
                        candidates.append((match.group(1), line_top, line_left, True))
                        continue

                    # Extract handwritten digit only from the SAME refills line and to the RIGHT of "or"
                    line_words = []
                    for blk in blocks_for_page:
                        if blk.get("BlockType") != "WORD":
                            continue
                        if blk.get("Page", 1) != page:
                            continue
                        bbox = blk.get("Geometry", {}).get("BoundingBox", {})
                        blk_top = bbox.get("Top", 0)
                        blk_left = bbox.get("Left", 0)
                        if blk_left < 0.70:
                            continue
                        if abs(blk_top - line_top) > 0.02:
                            continue
                        word_text = blk.get("Text", "")
                        if word_text:
                            line_words.append((blk_left, word_text))

                    if line_words:
                        line_words.sort(key=lambda x: x[0])
                        or_left = None
                        for left, word in line_words:
                            if word.lower() == "or":
                                or_left = left
                                break
                        for left, word in line_words:
                            if or_left is not None and left <= or_left:
                                continue
                            if word.isdigit() and word != "12":
                                candidates.append((word, line_top, left, False))

                if not candidates:
                    return None

                def score(item):
                    value, line_top, line_left, _has_inline = item
                    return abs(line_top - top) + abs(line_left - 0.90)

                candidates.sort(key=score)
                value = candidates[0][0]
                return f"12 or {value}"
            
            # Determine patient_type and dosage using product row anchors and section headers
            nearest_row = None
            nearest_row_distance = None
            for row in product_rows:
                if row["page"] != checkbox_page:
                    continue
                distance = abs(row["top"] - checkbox_top)
                if nearest_row_distance is None or distance < nearest_row_distance:
                    nearest_row_distance = distance
                    nearest_row = row

            if nearest_row and nearest_row.get("dosage"):
                checkbox_info["dosage"] = nearest_row["dosage"]
                if nearest_row.get("patient_type"):
                    checkbox_info["patient_type"] = nearest_row["patient_type"]

            if not checkbox_info["patient_type"]:
                nearest_header = None
                nearest_header_top = None
                for header in section_headers:
                    if header["page"] != checkbox_page:
                        continue
                    if header["top"] <= checkbox_top:
                        if nearest_header_top is None or header["top"] > nearest_header_top:
                            nearest_header_top = header["top"]
                            nearest_header = header
                if nearest_header:
                    checkbox_info["patient_type"] = nearest_header["patient_type"]

            if not checkbox_info["patient_type"]:
                if any(marker in context for marker in ["pediatric", "wt<50", "wt <50", "wt≥50", "wt ≥50", "wt<50kg"]):
                    checkbox_info["patient_type"] = "pediatric"
                else:
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
            elif not checkbox_info["dosage"]:
                if "(2x150" in context:  # 2x150 = 300mg total
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
            
            # Classify checkbox type: DEVICE (product) vs DOSING (regimen)
            # Use spatial relationship to nearby text labels (no fixed coordinates).
            device_candidates = []
            dosing_candidates = []

            def add_device_candidate(text_block):
                block_text = text_block["text"].lower()
                if "unoready" in block_text:
                    device_candidates.append(("unoready_pen", text_block["distance"]))
                elif "sensoready" in block_text:
                    device_candidates.append(("sensoready_pen", text_block["distance"]))
                elif "prefilled syringe" in block_text or ("prefilled" in block_text and "syringe" in block_text):
                    device_candidates.append(("syringe", text_block["distance"]))
                elif "syringe" in block_text:
                    device_candidates.append(("syringe", text_block["distance"]))

            def add_dosing_candidate(text_block):
                block_text = text_block["text"].lower()
                if any(header in block_text for header in ["dosage/quantity", "product information", "refills"]):
                    return
                if "maintenance increase" in block_text or "every 2 weeks" in block_text:
                    dosing_candidates.append(("maintenance_increase", text_block["distance"]))
                elif "maintenance" in block_text and "loading" not in block_text:
                    dosing_candidates.append(("maintenance", text_block["distance"]))
                elif "loading dose" in block_text or "loading" in block_text:
                    if "loading dose already completed" not in block_text:
                        dosing_candidates.append(("loading", text_block["distance"]))

            # Prefer closest text for dosing when it has clear keywords
            dose_type_from_closest = None
            if "maintenance increase" in closest_text or "every 2 weeks" in closest_text:
                dose_type_from_closest = "maintenance_increase"
            elif ("maintenance" in closest_text and "loading" not in closest_text) or "every 4 weeks" in closest_text:
                dose_type_from_closest = "maintenance"
            elif "loading dose" in closest_text or "loading" in closest_text:
                if "loading dose already completed" not in closest_text:
                    dose_type_from_closest = "loading"

            if dose_type_from_closest:
                checkbox_info["type"] = "dosing"
                checkbox_info["dose_type"] = dose_type_from_closest
            else:
                for text_block in same_row_text_blocks[:10]:
                    add_device_candidate(text_block)
                    add_dosing_candidate(text_block)

                if not device_candidates and not dosing_candidates:
                    for text_block in nearby_text_blocks[:10]:
                        add_device_candidate(text_block)
                        add_dosing_candidate(text_block)

                device_candidates.sort(key=lambda x: x[1])
                dosing_candidates.sort(key=lambda x: x[1])

                if device_candidates or dosing_candidates:
                    device_choice = device_candidates[0] if device_candidates else None
                    dosing_choice = dosing_candidates[0] if dosing_candidates else None

                    if device_choice and (not dosing_choice or device_choice[1] <= dosing_choice[1]):
                        checkbox_info["type"] = "device"
                        checkbox_info["form"] = device_choice[0]
                    elif dosing_choice:
                        checkbox_info["type"] = "dosing"
                        checkbox_info["dose_type"] = dosing_choice[0]
            # Note: Refills checkboxes handled via table parsing above

            if checkbox_info["type"] == "dosing" and checkbox_info["dose_type"] in ["maintenance", "maintenance_increase"]:
                refills_from_blocks = _find_refills_near_checkbox(checkbox_page, checkbox_top, blocks)
                if refills_from_blocks:
                    checkbox_info["refills"] = refills_from_blocks
            
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
        
        # No exclusivity enforcement: allow multiple dosages and multiple selections per section.
        for key, group in groups.items():
            num_devices = len(group['devices'])
            num_dosings = len(group['dosings'])
            num_prescriptions = num_devices * num_dosings
            
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
                    if dosing.get("refills"):
                        matching_refills = dosing.get("refills")
                    if dosing["dose_type"] in ["maintenance", "maintenance_increase"]:
                        # Match refills by patient_type AND dosage AND dose_type
                        if not matching_refills:
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
            if dosage == "300mg":
                form_display = "Sensoready Pen (2x150 mg/mL)"
            elif dosage == "150mg":
                form_display = "Sensoready Pen (1x150 mg/mL)"
            else:
                form_display = "Sensoready Pen"
        elif form == "unoready_pen":
            form_display = "UnoReady Pen (1x300 mg/2 mL)"
        elif form == "syringe":
            if dosage == "300mg":
                form_display = "Prefilled Syringe (2x150 mg/mL)"
            elif dosage == "150mg":
                form_display = "Prefilled Syringe (1x150 mg/mL)"
            elif dosage == "75mg":
                form_display = "Prefilled Syringe (1x75 mg/mL)"
            else:
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
        
        # Calculate quantity based on dosing schedule and device strength
        doses_per_28_days = 1
        if dose_type == "loading":
            doses_per_28_days = 4
        elif dose_type == "maintenance_increase":
            doses_per_28_days = 2

        units_per_dose = 1
        if dosage == "300mg":
            if form in ["sensoready_pen", "syringe"]:
                units_per_dose = 2
            else:
                units_per_dose = 1

        quantity_value = str(doses_per_28_days * units_per_dose)

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
                value=quantity_value,
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
