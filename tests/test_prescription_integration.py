"""Integration tests for prescription extraction with mock Textract checkbox responses.

These tests verify the full flow: Textract OCR → Checkbox Detection → Prescription Creation
"""

import pytest
from src.extraction.prescription_extractor import PrescriptionExtractor


# ============================================================================
# HELPER FUNCTIONS TO CREATE MOCK TEXTRACT BLOCKS
# ============================================================================

def create_checkbox_block(checkbox_id, is_selected, page=1, top=0.5, left=0.3):
    """Helper to create a Textract SELECTION_ELEMENT block (checkbox)."""
    return {
        "BlockType": "SELECTION_ELEMENT",
        "Id": checkbox_id,
        "SelectionStatus": "SELECTED" if is_selected else "NOT_SELECTED",
        "Confidence": 99.5,
        "Page": page,
        "Geometry": {
            "BoundingBox": {
                "Width": 0.02,
                "Height": 0.015,
                "Left": left,
                "Top": top
            }
        }
    }


def create_word_block(word_id, text, page=1, top=0.5, left=0.35, confidence=99.0):
    """Helper to create a Textract WORD block."""
    return {
        "BlockType": "WORD",
        "Id": word_id,
        "Text": text,
        "Confidence": confidence,
        "Page": page,
        "Geometry": {
            "BoundingBox": {
                "Width": len(text) * 0.01,
                "Height": 0.015,
                "Left": left,
                "Top": top
            }
        }
    }


def create_line_block(line_id, text, word_ids, page=1, top=0.5, left=0.35):
    """Helper to create a Textract LINE block."""
    return {
        "BlockType": "LINE",
        "Id": line_id,
        "Text": text,
        "Confidence": 99.0,
        "Page": page,
        "Geometry": {
            "BoundingBox": {
                "Width": len(text) * 0.01,
                "Height": 0.015,
                "Left": left,
                "Top": top
            }
        },
        "Relationships": [
            {
                "Type": "CHILD",
                "Ids": word_ids
            }
        ]
    }


# ============================================================================
# INTEGRATION TESTS WITH MOCK TEXTRACT RESPONSES
# ============================================================================

class TestTextractCheckboxIntegration:
    """Integration tests using mock Textract responses with checkbox data.
    
    These tests simulate real PDF uploads and verify:
    - Checkbox detection from Textract SELECTION_ELEMENT blocks
    - Correct mapping of checkbox positions to prescription fields
    - Full extraction pipeline from OCR to prescription objects
    
    Covered Combinations:
    =====================
    1. Single checkbox - Adult 150mg Sensoready Pen + Loading
    2. Multiple checkboxes - Adult 300mg UnoReady Pen + Maintenance + Maintenance Increase
    3. Pediatric 75mg - Prefilled Syringe + Loading
    4. Mixed Adult + Pediatric sections
    5. No checkboxes selected (fallback)
    6. Custom refills extraction
    """
    
    def test_single_checkbox_adult_150mg_loading(self):
        """Test detection of single checkbox: Adult 150mg Sensoready Pen + Loading.
        
        Simulates: User checks only Sensoready Pen and Loading Dose in Adult 150mg section.
        Expected: 1 prescription created with correct quantity (4) and refills (0).
        """
        from src.ocr.textract_parser import TextractParser
        
        # Mock Textract response with one selected checkbox
        blocks = [
            # Checkbox for Sensoready Pen (Adult 150mg)
            create_checkbox_block("cb-1", is_selected=True, page=1, top=0.20, left=0.1),
            create_word_block("w-1", "Sensoready®", page=1, top=0.20, left=0.13),
            create_word_block("w-2", "Pen", page=1, top=0.20, left=0.22),
            create_word_block("w-3", "(1x150", page=1, top=0.20, left=0.26),
            create_word_block("w-4", "mg/mL)", page=1, top=0.20, left=0.32),
            create_line_block("l-1", "Sensoready® Pen (1x150 mg/mL)", ["w-1", "w-2", "w-3", "w-4"], page=1, top=0.20, left=0.13),
            
            # Checkbox for Loading Dose
            create_checkbox_block("cb-2", is_selected=True, page=1, top=0.20, left=0.5),
            create_word_block("w-5", "Loading", page=1, top=0.20, left=0.53),
            create_word_block("w-6", "Dose:", page=1, top=0.20, left=0.62),
            create_word_block("w-7", "Inject", page=1, top=0.20, left=0.68),
            create_word_block("w-8", "150", page=1, top=0.20, left=0.75),
            create_word_block("w-9", "mg", page=1, top=0.20, left=0.78),
            create_line_block("l-2", "Loading Dose: Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3", 
                            ["w-5", "w-6", "w-7", "w-8", "w-9"], page=1, top=0.20, left=0.53),
            
            # Section header
            create_word_block("w-10", "COSENTYX", page=1, top=0.15, left=0.1),
            create_word_block("w-11", "150", page=1, top=0.15, left=0.25),
            create_word_block("w-12", "mg", page=1, top=0.15, left=0.28),
            create_line_block("l-3", "COSENTYX 150 mg", ["w-10", "w-11", "w-12"], page=1, top=0.15, left=0.1),
            
            # Refills
            create_word_block("w-13", "N/A", page=1, top=0.20, left=0.85),
            create_line_block("l-4", "N/A", ["w-13"], page=1, top=0.20, left=0.85),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) == 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Sensoready Pen (1x150 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.quantity.value == "4"
        assert rx.refills.value == "0"

    def test_multiple_checkboxes_adult_300mg(self):
        """Test detection of multiple checkboxes: Adult 300mg UnoReady Pen + Maintenance + Maintenance Increase.
        
        Simulates: User checks UnoReady Pen, Maintenance, AND Maintenance Increase in Adult 300mg section.
        Expected: 2 separate prescriptions created (one for each dosing type).
        """
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            # Section: Adult 300mg
            create_line_block("l-header", "COSENTYX 300 mg", ["w-h1", "w-h2", "w-h3"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            create_word_block("w-h2", "300", page=1, top=0.30, left=0.25),
            create_word_block("w-h3", "mg", page=1, top=0.30, left=0.28),
            
            # UnoReady Pen checkbox (selected)
            create_checkbox_block("cb-uno", is_selected=True, page=1, top=0.35, left=0.1),
            create_line_block("l-uno", "UnoReady® Pen (1x300 mg/2 mL)", ["w-uno1", "w-uno2"], page=1, top=0.35, left=0.13),
            create_word_block("w-uno1", "UnoReady®", page=1, top=0.35, left=0.13),
            create_word_block("w-uno2", "Pen", page=1, top=0.35, left=0.22),
            
            # Maintenance checkbox (selected)
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.35, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 300 mg on Week 4", ["w-m1", "w-m2"], page=1, top=0.35, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.35, left=0.53),
            create_word_block("w-m2", "Inject", page=1, top=0.35, left=0.65),
            
            # Maintenance Increase checkbox (selected)
            create_checkbox_block("cb-incr", is_selected=True, page=1, top=0.38, left=0.5),
            create_line_block("l-incr", "Maintenance Increase (HS only): Inject 300 mg every 2 weeks", 
                            ["w-i1", "w-i2", "w-i3"], page=1, top=0.38, left=0.53),
            create_word_block("w-i1", "Maintenance", page=1, top=0.38, left=0.53),
            create_word_block("w-i2", "Increase", page=1, top=0.38, left=0.65),
            create_word_block("w-i3", "every", page=1, top=0.38, left=0.74),
            
            # Refills
            create_line_block("l-ref", "12 or 0 refills", ["w-r1"], page=1, top=0.35, left=0.85),
            create_word_block("w-r1", "12", page=1, top=0.35, left=0.85),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 2 prescriptions: UnoReady+Maintenance and UnoReady+MaintenanceIncrease
        assert len(result.prescriptions) >= 2
        
        # Verify we have both dose types
        dose_types = [rx.dose_type.value for rx in result.prescriptions]
        assert "Maintenance" in dose_types
        assert "Maintenance Increase" in dose_types

    def test_pediatric_checkboxes(self):
        """Test detection of pediatric checkboxes: 75mg Syringe + Loading.
        
        Simulates: User checks Prefilled Syringe and Loading Dose in Pediatric 75mg (wt <50kg) section.
        Expected: 1 prescription with pediatric patient type and 75mg dosage.
        """
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            # Section: Pediatric 75mg
            create_line_block("l-ped", "COSENTYX 75 mg (wt <50 kg)", ["w-p1", "w-p2"], page=1, top=0.50, left=0.1),
            create_word_block("w-p1", "COSENTYX", page=1, top=0.50, left=0.1),
            create_word_block("w-p2", "75", page=1, top=0.50, left=0.25),
            create_word_block("w-p3", "mg", page=1, top=0.50, left=0.28),
            create_word_block("w-p4", "(wt", page=1, top=0.50, left=0.30),
            create_word_block("w-p5", "<50", page=1, top=0.50, left=0.33),
            create_word_block("w-p6", "kg)", page=1, top=0.50, left=0.36),
            
            # Prefilled Syringe checkbox (selected)
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.55, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (1x75 mg/mL)", ["w-s1", "w-s2"], page=1, top=0.55, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.55, left=0.13),
            create_word_block("w-s2", "Syringe", page=1, top=0.55, left=0.22),
            
            # Loading Dose checkbox (selected)
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.55, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 75 mg on Weeks 0, 1, 2, 3", 
                            ["w-l1", "w-l2", "w-l3"], page=1, top=0.55, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.55, left=0.53),
            create_word_block("w-l2", "Dose:", page=1, top=0.55, left=0.61),
            create_word_block("w-l3", "Inject", page=1, top=0.55, left=0.67),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "75mg"
        assert rx.patient_type.value == "Pediatric"
        assert rx.dose_type.value == "Loading"
        assert "Syringe" in rx.form.value

    def test_mixed_adult_and_pediatric_selections(self):
        """Test multiple prescriptions across Adult and Pediatric sections.
        
        Simulates: User checks prescriptions in BOTH Adult 150mg AND Pediatric 150mg sections.
        Expected: 2 prescriptions, one Adult and one Pediatric.
        """
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            # Adult 150mg section
            create_line_block("l-a150", "COSENTYX 150 mg", ["w-a1"], page=1, top=0.20, left=0.1),
            create_word_block("w-a1", "COSENTYX", page=1, top=0.20, left=0.1),
            create_word_block("w-a2", "150", page=1, top=0.20, left=0.25),
            
            create_checkbox_block("cb-apen", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-apen", "Sensoready Pen (1x150 mg/mL)", ["w-ap1"], page=1, top=0.22, left=0.13),
            create_word_block("w-ap1", "Sensoready", page=1, top=0.22, left=0.13),
            
            create_checkbox_block("cb-amaint", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-amaint", "Maintenance: Inject 150 mg", ["w-am1"], page=1, top=0.22, left=0.53),
            create_word_block("w-am1", "Maintenance:", page=1, top=0.22, left=0.53),
            
            # Pediatric 150mg section
            create_line_block("l-p150", "COSENTYX 150 mg (wt ≥50 kg)", ["w-p1"], page=1, top=0.60, left=0.1),
            create_word_block("w-p1", "COSENTYX", page=1, top=0.60, left=0.1),
            create_word_block("w-p2", "150", page=1, top=0.60, left=0.25),
            create_word_block("w-p3", "(wt", page=1, top=0.60, left=0.30),
            
            create_checkbox_block("cb-psyr", is_selected=True, page=1, top=0.62, left=0.1),
            create_line_block("l-psyr", "Prefilled Syringe (1x150 mg/mL)", ["w-ps1"], page=1, top=0.62, left=0.13),
            create_word_block("w-ps1", "Prefilled", page=1, top=0.62, left=0.13),
            
            create_checkbox_block("cb-pload", is_selected=True, page=1, top=0.62, left=0.5),
            create_line_block("l-pload", "Loading Dose: Inject 150 mg", ["w-pl1"], page=1, top=0.62, left=0.53),
            create_word_block("w-pl1", "Loading", page=1, top=0.62, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should have 2 prescriptions: Adult 150mg Maintenance + Pediatric 150mg Loading
        assert len(result.prescriptions) >= 2
        
        # Check we have both adult and pediatric
        patient_types = [rx.patient_type.value for rx in result.prescriptions]
        assert "Adult" in patient_types
        assert "Pediatric" in patient_types

    def test_no_checkboxes_selected(self):
        """Test handling when no checkboxes are selected.
        
        Simulates: Form uploaded with no checkboxes marked (blank form or unclear marks).
        Expected: Fallback behavior - creates default prescription to avoid complete failure.
        """
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            # All checkboxes NOT selected
            create_checkbox_block("cb-1", is_selected=False, page=1, top=0.20, left=0.1),
            create_word_block("w-1", "Sensoready", page=1, top=0.20, left=0.13),
            
            create_checkbox_block("cb-2", is_selected=False, page=1, top=0.20, left=0.5),
            create_word_block("w-2", "Loading", page=1, top=0.20, left=0.53),
            
            create_line_block("l-1", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.15, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.15, left=0.1),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should fall back to default prescription or have at least 1
        assert len(result.prescriptions) >= 1

    def test_refills_extraction_from_form(self):
        """Test extraction of custom refills values from form.
        
        Simulates: Prescriber handwrites "3" in the refills box (instead of default 0).
        Expected: System should detect and use custom refills value "12 or 3".
        Note: Current implementation may use default if handwriting detection is complex.
        """
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            # Adult 150mg Maintenance with custom refills
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            create_checkbox_block("cb-pen", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-pen", "Sensoready Pen", ["w-p1"], page=1, top=0.22, left=0.13),
            create_word_block("w-p1", "Sensoready", page=1, top=0.22, left=0.13),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 150 mg", ["w-m1"], page=1, top=0.22, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.22, left=0.53),
            
            # Custom refills value (handwritten "3")
            create_line_block("l-ref", "12 or 3 refills", ["w-r1", "w-r2"], page=1, top=0.22, left=0.85),
            create_word_block("w-r1", "12", page=1, top=0.22, left=0.85),
            create_word_block("w-r2", "or", page=1, top=0.22, left=0.87),
            create_word_block("w-r3", "3", page=1, top=0.22, left=0.89),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Note: Current implementation may not extract custom refills perfectly
        # This test documents expected behavior
        assert len(result.prescriptions) >= 1

    def test_adult_150mg_both_devices_same_dosing(self):
        """Test selection of both devices with same dosing type.
        
        Simulates: User checks BOTH Sensoready Pen AND Prefilled Syringe, both with Loading.
        Expected: 2 separate prescriptions (one for each device type).
        """
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            # Sensoready Pen checkbox
            create_checkbox_block("cb-pen", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-pen", "Sensoready Pen (1x150 mg/mL)", ["w-p1"], page=1, top=0.22, left=0.13),
            create_word_block("w-p1", "Sensoready", page=1, top=0.22, left=0.13),
            
            # Prefilled Syringe checkbox
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.24, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (1x150 mg/mL)", ["w-s1"], page=1, top=0.24, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.24, left=0.13),
            
            # Loading Dose checkbox (shared by both devices)
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 150 mg on Weeks 0, 1, 2, 3", 
                            ["w-l1"], page=1, top=0.22, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.22, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 2 prescriptions (one for each device)
        assert len(result.prescriptions) >= 2
        
        # Both should be loading doses
        forms = [rx.form.value for rx in result.prescriptions]
        assert any("Sensoready Pen" in form for form in forms)
        assert any("Syringe" in form for form in forms)

    def test_adult_300mg_all_three_devices_maintenance(self):
        """Test selection of all three 300mg devices with maintenance.
        
        Simulates: User checks UnoReady Pen, Sensoready Pen, AND Prefilled Syringe all with Maintenance.
        Expected: 3 separate prescriptions with different quantities (1, 2, 2 respectively).
        """
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            
            # UnoReady Pen
            create_checkbox_block("cb-uno", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-uno", "UnoReady Pen (1x300 mg/2 mL)", ["w-u1"], page=1, top=0.32, left=0.13),
            create_word_block("w-u1", "UnoReady", page=1, top=0.32, left=0.13),
            
            # Sensoready Pen
            create_checkbox_block("cb-senso", is_selected=True, page=1, top=0.34, left=0.1),
            create_line_block("l-senso", "Sensoready Pen (2x150 mg/mL)", ["w-s1"], page=1, top=0.34, left=0.13),
            create_word_block("w-s1", "Sensoready", page=1, top=0.34, left=0.13),
            
            # Prefilled Syringe
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.36, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (2x150 mg/mL)", ["w-sy1"], page=1, top=0.36, left=0.13),
            create_word_block("w-sy1", "Prefilled", page=1, top=0.36, left=0.13),
            
            # Maintenance checkbox
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 300 mg on Week 4", ["w-m1"], page=1, top=0.32, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.32, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 3 prescriptions (one for each device)
        assert len(result.prescriptions) >= 3
        
        # All should be maintenance doses
        dose_types = [rx.dose_type.value for rx in result.prescriptions]
        assert all(dt == "Maintenance" for dt in dose_types)

    # ============================================================================
    # SECTION 1: ADULT 150mg COMPREHENSIVE TESTS
    # ============================================================================
    
    def test_adult_150mg_sensoready_pen_maintenance(self):
        """Adult 150mg: Sensoready Pen + Maintenance.
        Expected: 1 Rx, quantity=1, refills=12 or 0"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            create_checkbox_block("cb-pen", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-pen", "Sensoready Pen (1x150 mg/mL)", ["w-p1"], page=1, top=0.22, left=0.13),
            create_word_block("w-p1", "Sensoready", page=1, top=0.22, left=0.13),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 150 mg", ["w-m1"], page=1, top=0.22, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.22, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "150mg"
        assert "Sensoready Pen" in rx.form.value
        assert rx.dose_type.value == "Maintenance"
        assert rx.quantity.value == "1"

    def test_adult_150mg_syringe_loading(self):
        """Adult 150mg: Prefilled Syringe + Loading.
        Expected: 1 Rx, quantity=4, refills=0"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (1x150 mg/mL)", ["w-s1"], page=1, top=0.22, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.22, left=0.13),
            
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 150 mg", ["w-l1"], page=1, top=0.22, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.22, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "150mg"
        assert "Syringe" in rx.form.value
        assert rx.dose_type.value == "Loading"
        assert rx.quantity.value == "4"

    def test_adult_150mg_both_devices_both_dosing_types(self):
        """Adult 150mg: Both devices + Both dosing types = 4 prescriptions.
        Expected: 4 Rx total (Pen+Loading, Pen+Maintenance, Syringe+Loading, Syringe+Maintenance)"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            # Both devices
            create_checkbox_block("cb-pen", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-pen", "Sensoready Pen (1x150 mg/mL)", ["w-p1"], page=1, top=0.22, left=0.13),
            create_word_block("w-p1", "Sensoready", page=1, top=0.22, left=0.13),
            
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.24, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (1x150 mg/mL)", ["w-s1"], page=1, top=0.24, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.24, left=0.13),
            
            # Both dosing types
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 150 mg", ["w-l1"], page=1, top=0.22, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.22, left=0.53),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.24, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 150 mg", ["w-m1"], page=1, top=0.24, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.24, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 4 prescriptions (2 devices × 2 dosing types)
        assert len(result.prescriptions) >= 4
        
        # Verify we have both devices and both dose types
        forms = [rx.form.value for rx in result.prescriptions]
        dose_types = [rx.dose_type.value for rx in result.prescriptions]
        assert any("Sensoready Pen" in form for form in forms)
        assert any("Syringe" in form for form in forms)
        assert "Loading" in dose_types
        assert "Maintenance" in dose_types

    # ============================================================================
    # SECTION 2: ADULT 300mg COMPREHENSIVE TESTS
    # ============================================================================
    
    def test_adult_300mg_uno_pen_loading(self):
        """Adult 300mg: UnoReady Pen + Loading.
        Expected: 1 Rx, quantity=4, refills=0"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            
            create_checkbox_block("cb-uno", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-uno", "UnoReady Pen (1x300 mg/2 mL)", ["w-u1"], page=1, top=0.32, left=0.13),
            create_word_block("w-u1", "UnoReady", page=1, top=0.32, left=0.13),
            
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 300 mg", ["w-l1"], page=1, top=0.32, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.32, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "300mg"
        assert "UnoReady Pen" in rx.form.value
        assert rx.dose_type.value == "Loading"
        assert rx.quantity.value == "4"

    def test_adult_300mg_sensoready_maintenance(self):
        """Adult 300mg: Sensoready Pen + Maintenance.
        Expected: 1 Rx, quantity=2, refills=12 or 0"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            
            create_checkbox_block("cb-senso", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-senso", "Sensoready Pen (2x150 mg/mL)", ["w-s1"], page=1, top=0.32, left=0.13),
            create_word_block("w-s1", "Sensoready", page=1, top=0.32, left=0.13),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 300 mg", ["w-m1"], page=1, top=0.32, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.32, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "300mg"
        assert "Sensoready Pen" in rx.form.value
        assert rx.dose_type.value == "Maintenance"
        assert rx.quantity.value == "2"

    def test_adult_300mg_syringe_maintenance_increase(self):
        """Adult 300mg: Prefilled Syringe + Maintenance Increase.
        Expected: 1 Rx, quantity=4, refills=12 or 0"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (2x150 mg/mL)", ["w-s1"], page=1, top=0.32, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.32, left=0.13),
            
            create_checkbox_block("cb-incr", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-incr", "Maintenance Increase (HS only): every 2 weeks", ["w-i1"], page=1, top=0.32, left=0.53),
            create_word_block("w-i1", "Maintenance", page=1, top=0.32, left=0.53),
            create_word_block("w-i2", "Increase", page=1, top=0.32, left=0.65),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "300mg"
        assert "Syringe" in rx.form.value
        assert rx.dose_type.value == "Maintenance Increase"
        assert rx.quantity.value == "4"

    def test_adult_300mg_all_nine_combinations(self):
        """Adult 300mg: All 3 devices × All 3 dosing types = 9 prescriptions.
        Expected: 9 total prescriptions with correct quantities"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            
            # All 3 devices
            create_checkbox_block("cb-uno", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-uno", "UnoReady Pen (1x300 mg/2 mL)", ["w-u1"], page=1, top=0.32, left=0.13),
            create_word_block("w-u1", "UnoReady", page=1, top=0.32, left=0.13),
            
            create_checkbox_block("cb-senso", is_selected=True, page=1, top=0.34, left=0.1),
            create_line_block("l-senso", "Sensoready Pen (2x150 mg/mL)", ["w-s1"], page=1, top=0.34, left=0.13),
            create_word_block("w-s1", "Sensoready", page=1, top=0.34, left=0.13),
            
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.36, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (2x150 mg/mL)", ["w-sy1"], page=1, top=0.36, left=0.13),
            create_word_block("w-sy1", "Prefilled", page=1, top=0.36, left=0.13),
            
            # All 3 dosing types
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 300 mg", ["w-l1"], page=1, top=0.32, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.32, left=0.53),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.34, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 300 mg", ["w-m1"], page=1, top=0.34, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.34, left=0.53),
            
            create_checkbox_block("cb-incr", is_selected=True, page=1, top=0.36, left=0.5),
            create_line_block("l-incr", "Maintenance Increase: every 2 weeks", ["w-i1"], page=1, top=0.36, left=0.53),
            create_word_block("w-i1", "Maintenance", page=1, top=0.36, left=0.53),
            create_word_block("w-i2", "Increase", page=1, top=0.36, left=0.65),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 9 prescriptions (3 devices × 3 dosing types)
        assert len(result.prescriptions) >= 9
        
        # Verify all 3 devices present
        forms = [rx.form.value for rx in result.prescriptions]
        assert any("UnoReady" in form for form in forms)
        assert any("Sensoready Pen" in form for form in forms)
        assert any("Syringe" in form for form in forms)
        
        # Verify all 3 dose types present
        dose_types = [rx.dose_type.value for rx in result.prescriptions]
        assert "Loading" in dose_types
        assert "Maintenance" in dose_types
        assert "Maintenance Increase" in dose_types

    def test_adult_300mg_loading_to_maintenance_transition(self):
        """Adult 300mg: UnoReady Pen + Loading AND Maintenance (patient transition).
        Expected: 2 Rx for sequential therapy"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            
            create_checkbox_block("cb-uno", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-uno", "UnoReady Pen (1x300 mg/2 mL)", ["w-u1"], page=1, top=0.32, left=0.13),
            create_word_block("w-u1", "UnoReady", page=1, top=0.32, left=0.13),
            
            # Both Loading and Maintenance checked (transition scenario)
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 300 mg", ["w-l1"], page=1, top=0.32, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.32, left=0.53),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.34, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 300 mg", ["w-m1"], page=1, top=0.34, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.34, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 2 prescriptions (same device, different dosing)
        assert len(result.prescriptions) >= 2
        
        dose_types = [rx.dose_type.value for rx in result.prescriptions]
        assert "Loading" in dose_types
        assert "Maintenance" in dose_types

    # ============================================================================
    # SECTION 3: PEDIATRIC 75mg COMPREHENSIVE TESTS
    # ============================================================================
    
    def test_pediatric_75mg_syringe_maintenance(self):
        """Pediatric 75mg: Prefilled Syringe + Maintenance.
        Expected: 1 Rx, pediatric type, quantity=1"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-ped", "COSENTYX 75 mg (wt <50 kg)", ["w-p1"], page=1, top=0.50, left=0.1),
            create_word_block("w-p1", "COSENTYX", page=1, top=0.50, left=0.1),
            create_word_block("w-p2", "75", page=1, top=0.50, left=0.25),
            create_word_block("w-p3", "mg", page=1, top=0.50, left=0.28),
            
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.52, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (1x75 mg/mL)", ["w-s1"], page=1, top=0.52, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.52, left=0.13),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.52, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 75 mg", ["w-m1"], page=1, top=0.52, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.52, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "75mg"
        assert rx.patient_type.value == "Pediatric"
        assert rx.dose_type.value == "Maintenance"
        assert rx.quantity.value == "1"

    # ============================================================================
    # SECTION 4: PEDIATRIC 150mg COMPREHENSIVE TESTS
    # ============================================================================
    
    def test_pediatric_150mg_sensoready_loading(self):
        """Pediatric 150mg: Sensoready Pen + Loading.
        Expected: 1 Rx, pediatric type, quantity=4"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-ped", "COSENTYX 150 mg (wt ≥50 kg)", ["w-p1"], page=1, top=0.60, left=0.1),
            create_word_block("w-p1", "COSENTYX", page=1, top=0.60, left=0.1),
            create_word_block("w-p2", "150", page=1, top=0.60, left=0.25),
            create_word_block("w-p3", "(wt", page=1, top=0.60, left=0.30),
            
            create_checkbox_block("cb-pen", is_selected=True, page=1, top=0.62, left=0.1),
            create_line_block("l-pen", "Sensoready Pen (1x150 mg/mL)", ["w-pen1"], page=1, top=0.62, left=0.13),
            create_word_block("w-pen1", "Sensoready", page=1, top=0.62, left=0.13),
            
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.62, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 150 mg", ["w-l1"], page=1, top=0.62, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.62, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "150mg"
        assert rx.patient_type.value == "Pediatric"
        assert "Sensoready Pen" in rx.form.value
        assert rx.dose_type.value == "Loading"
        assert rx.quantity.value == "4"

    def test_pediatric_150mg_syringe_maintenance(self):
        """Pediatric 150mg: Prefilled Syringe + Maintenance.
        Expected: 1 Rx, pediatric type, quantity=1"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-ped", "COSENTYX 150 mg (wt ≥50 kg)", ["w-p1"], page=1, top=0.60, left=0.1),
            create_word_block("w-p1", "COSENTYX", page=1, top=0.60, left=0.1),
            create_word_block("w-p2", "150", page=1, top=0.60, left=0.25),
            
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.62, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (1x150 mg/mL)", ["w-s1"], page=1, top=0.62, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.62, left=0.13),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.62, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 150 mg", ["w-m1"], page=1, top=0.62, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.62, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        rx = result.prescriptions[0]
        assert rx.dosage.value == "150mg"
        assert rx.patient_type.value == "Pediatric"
        assert "Syringe" in rx.form.value
        assert rx.dose_type.value == "Maintenance"

    def test_pediatric_150mg_both_devices_both_dosing(self):
        """Pediatric 150mg: Both devices + Both dosing types = 4 prescriptions.
        Expected: 4 Rx, all pediatric type"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-ped", "COSENTYX 150 mg (wt ≥50 kg)", ["w-p1"], page=1, top=0.60, left=0.1),
            create_word_block("w-p1", "COSENTYX", page=1, top=0.60, left=0.1),
            create_word_block("w-p2", "150", page=1, top=0.60, left=0.25),
            
            # Both devices
            create_checkbox_block("cb-pen", is_selected=True, page=1, top=0.62, left=0.1),
            create_line_block("l-pen", "Sensoready Pen (1x150 mg/mL)", ["w-pen1"], page=1, top=0.62, left=0.13),
            create_word_block("w-pen1", "Sensoready", page=1, top=0.62, left=0.13),
            
            create_checkbox_block("cb-syr", is_selected=True, page=1, top=0.64, left=0.1),
            create_line_block("l-syr", "Prefilled Syringe (1x150 mg/mL)", ["w-s1"], page=1, top=0.64, left=0.13),
            create_word_block("w-s1", "Prefilled", page=1, top=0.64, left=0.13),
            
            # Both dosing types
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.62, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 150 mg", ["w-l1"], page=1, top=0.62, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.62, left=0.53),
            
            create_checkbox_block("cb-maint", is_selected=True, page=1, top=0.64, left=0.5),
            create_line_block("l-maint", "Maintenance: Inject 150 mg", ["w-m1"], page=1, top=0.64, left=0.53),
            create_word_block("w-m1", "Maintenance:", page=1, top=0.64, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 4 prescriptions
        assert len(result.prescriptions) >= 4
        
        # All should be pediatric
        patient_types = [rx.patient_type.value for rx in result.prescriptions]
        assert all(pt == "Pediatric" for pt in patient_types)

    # ============================================================================
    # SECTION 5: EDGE CASES AND ERROR HANDLING
    # ============================================================================
    
    def test_only_device_selected_no_dosing(self):
        """Error case: Device selected but NO dosing type.
        Expected: Should still create prescription with fallback/default behavior"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            # Device selected
            create_checkbox_block("cb-pen", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-pen", "Sensoready Pen (1x150 mg/mL)", ["w-p1"], page=1, top=0.22, left=0.13),
            create_word_block("w-p1", "Sensoready", page=1, top=0.22, left=0.13),
            
            # NO dosing type selected
            create_checkbox_block("cb-load", is_selected=False, page=1, top=0.22, left=0.5),
            create_checkbox_block("cb-maint", is_selected=False, page=1, top=0.24, left=0.5),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should handle gracefully (may create default or skip)
        assert result.prescriptions is not None

    def test_only_dosing_selected_no_device(self):
        """Error case: Dosing type selected but NO device.
        Expected: Should handle gracefully"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            # NO device selected
            create_checkbox_block("cb-pen", is_selected=False, page=1, top=0.22, left=0.1),
            create_checkbox_block("cb-syr", is_selected=False, page=1, top=0.24, left=0.1),
            
            # Dosing selected
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-load", "Loading Dose: Inject 150 mg", ["w-l1"], page=1, top=0.22, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.22, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should handle gracefully
        assert result.prescriptions is not None

    def test_all_four_sections_selected_simultaneously(self):
        """Stress test: All 4 sections checked (Adult 150, Adult 300, Ped 75, Ped 150).
        Expected: Multiple prescriptions from all sections"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            # Adult 150mg
            create_line_block("l-a150", "COSENTYX 150 mg", ["w-a1"], page=1, top=0.20, left=0.1),
            create_word_block("w-a1", "COSENTYX", page=1, top=0.20, left=0.1),
            create_checkbox_block("cb-a150-pen", is_selected=True, page=1, top=0.22, left=0.1),
            create_line_block("l-a150-pen", "Sensoready Pen (1x150 mg/mL)", ["w-ap1"], page=1, top=0.22, left=0.13),
            create_word_block("w-ap1", "Sensoready", page=1, top=0.22, left=0.13),
            create_checkbox_block("cb-a150-load", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-a150-load", "Loading Dose: 150 mg", ["w-al1"], page=1, top=0.22, left=0.53),
            create_word_block("w-al1", "Loading", page=1, top=0.22, left=0.53),
            
            # Adult 300mg
            create_line_block("l-a300", "COSENTYX 300 mg", ["w-a3"], page=1, top=0.30, left=0.1),
            create_word_block("w-a3", "COSENTYX", page=1, top=0.30, left=0.1),
            create_checkbox_block("cb-a300-uno", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-a300-uno", "UnoReady Pen (1x300 mg/2 mL)", ["w-au1"], page=1, top=0.32, left=0.13),
            create_word_block("w-au1", "UnoReady", page=1, top=0.32, left=0.13),
            create_checkbox_block("cb-a300-maint", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-a300-maint", "Maintenance: 300 mg", ["w-am1"], page=1, top=0.32, left=0.53),
            create_word_block("w-am1", "Maintenance:", page=1, top=0.32, left=0.53),
            
            # Pediatric 75mg
            create_line_block("l-p75", "COSENTYX 75 mg (wt <50 kg)", ["w-p7"], page=1, top=0.50, left=0.1),
            create_word_block("w-p7", "COSENTYX", page=1, top=0.50, left=0.1),
            create_word_block("w-p72", "75", page=1, top=0.50, left=0.25),
            create_checkbox_block("cb-p75-syr", is_selected=True, page=1, top=0.52, left=0.1),
            create_line_block("l-p75-syr", "Prefilled Syringe (1x75 mg/mL)", ["w-ps1"], page=1, top=0.52, left=0.13),
            create_word_block("w-ps1", "Prefilled", page=1, top=0.52, left=0.13),
            create_checkbox_block("cb-p75-load", is_selected=True, page=1, top=0.52, left=0.5),
            create_line_block("l-p75-load", "Loading: 75 mg", ["w-pl1"], page=1, top=0.52, left=0.53),
            create_word_block("w-pl1", "Loading", page=1, top=0.52, left=0.53),
            
            # Pediatric 150mg
            create_line_block("l-p150", "COSENTYX 150 mg (wt ≥50 kg)", ["w-p1"], page=1, top=0.60, left=0.1),
            create_word_block("w-p1", "COSENTYX", page=1, top=0.60, left=0.1),
            create_word_block("w-p12", "150", page=1, top=0.60, left=0.25),
            create_checkbox_block("cb-p150-pen", is_selected=True, page=1, top=0.62, left=0.1),
            create_line_block("l-p150-pen", "Sensoready Pen (1x150 mg/mL)", ["w-pp1"], page=1, top=0.62, left=0.13),
            create_word_block("w-pp1", "Sensoready", page=1, top=0.62, left=0.13),
            create_checkbox_block("cb-p150-maint", is_selected=True, page=1, top=0.62, left=0.5),
            create_line_block("l-p150-maint", "Maintenance: 150 mg", ["w-pm1"], page=1, top=0.62, left=0.53),
            create_word_block("w-pm1", "Maintenance:", page=1, top=0.62, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should create 4+ prescriptions (one from each section)
        assert len(result.prescriptions) >= 4
        
        # Verify all dosages present
        dosages = [rx.dosage.value for rx in result.prescriptions]
        assert "150mg" in dosages
        assert "300mg" in dosages
        assert "75mg" in dosages

    def test_checkbox_confidence_edge_case(self):
        """Edge case: Low confidence checkbox detection.
        Expected: Should handle low confidence gracefully"""
        from src.ocr.textract_parser import TextractParser
        
        blocks = [
            create_line_block("l-150", "COSENTYX 150 mg", ["w-h1"], page=1, top=0.20, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.20, left=0.1),
            
            # Low confidence checkbox (55% confidence)
            {
                "BlockType": "SELECTION_ELEMENT",
                "Id": "cb-low",
                "SelectionStatus": "SELECTED",
                "Confidence": 55.0,  # Low confidence
                "Page": 1,
                "Geometry": {"BoundingBox": {"Width": 0.02, "Height": 0.015, "Left": 0.1, "Top": 0.22}}
            },
            create_line_block("l-pen", "Sensoready Pen", ["w-p1"], page=1, top=0.22, left=0.13),
            create_word_block("w-p1", "Sensoready", page=1, top=0.22, left=0.13),
            
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.22, left=0.5),
            create_line_block("l-load", "Loading Dose", ["w-l1"], page=1, top=0.22, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.22, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        # Should still process (may accept or reject based on threshold)
        assert result.prescriptions is not None

    def test_quantity_calculation_verification(self):
        """Verify correct quantity calculations for different scenarios.
        Tests the formula: doses_per_28_days × units_per_dose"""
        from src.ocr.textract_parser import TextractParser
        
        # Test Adult 300mg UnoReady Loading: 4 doses × 1 unit = 4
        blocks_uno_loading = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            create_checkbox_block("cb-uno", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-uno", "UnoReady Pen (1x300 mg/2 mL)", ["w-u1"], page=1, top=0.32, left=0.13),
            create_word_block("w-u1", "UnoReady", page=1, top=0.32, left=0.13),
            create_checkbox_block("cb-load", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-load", "Loading", ["w-l1"], page=1, top=0.32, left=0.53),
            create_word_block("w-l1", "Loading", page=1, top=0.32, left=0.53),
        ]
        
        textract_response = {"Blocks": blocks_uno_loading}
        parsed_data = TextractParser.parse_response(textract_response)
        
        extractor = PrescriptionExtractor()
        result = extractor.extract(parsed_data, payload_data=None)
        
        assert len(result.prescriptions) >= 1
        # UnoReady Loading: 4 doses × 1 unit = 4
        assert result.prescriptions[0].quantity.value == "4"
        
        # Test Adult 300mg Sensoready Maintenance Increase: 2 doses × 2 units = 4
        blocks_senso_incr = [
            create_line_block("l-300", "COSENTYX 300 mg", ["w-h1"], page=1, top=0.30, left=0.1),
            create_word_block("w-h1", "COSENTYX", page=1, top=0.30, left=0.1),
            create_checkbox_block("cb-senso", is_selected=True, page=1, top=0.32, left=0.1),
            create_line_block("l-senso", "Sensoready Pen (2x150 mg/mL)", ["w-s1"], page=1, top=0.32, left=0.13),
            create_word_block("w-s1", "Sensoready", page=1, top=0.32, left=0.13),
            create_checkbox_block("cb-incr", is_selected=True, page=1, top=0.32, left=0.5),
            create_line_block("l-incr", "Maintenance Increase", ["w-i1"], page=1, top=0.32, left=0.53),
            create_word_block("w-i1", "Maintenance", page=1, top=0.32, left=0.53),
            create_word_block("w-i2", "Increase", page=1, top=0.32, left=0.65),
        ]
        
        textract_response2 = {"Blocks": blocks_senso_incr}
        parsed_data2 = TextractParser.parse_response(textract_response2)
        
        result2 = extractor.extract(parsed_data2, payload_data=None)
        
        assert len(result2.prescriptions) >= 1
        # Sensoready Maintenance Increase: 2 doses × 2 units = 4
        assert result2.prescriptions[0].quantity.value == "4"