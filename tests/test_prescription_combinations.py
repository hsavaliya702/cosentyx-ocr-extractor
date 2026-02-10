"""Tests for prescription combinations and quantity rules based on checkbox selections."""

import pytest
import itertools

from src.extraction.prescription_extractor import PrescriptionExtractor


def _build_prescriptions(extractor, patient_type, dosage, devices, dosings):
    """Helper to build prescription combinations."""
    combos = []
    for form, dose_type in itertools.product(devices, dosings):
        combos.append(
            {
                "dosage": dosage,
                "patient_type": patient_type,
                "form": form,
                "dose_type": dose_type,
            }
        )
    return [extractor._create_prescription(combo) for combo in combos]


# ============================================================================
# ADULT 150mg SECTION TESTS
# ============================================================================

class TestAdult150mgCombinations:
    """Test all checkbox combinations for Adult COSENTYX 150mg section."""
    
    def test_adult_150mg_sensoready_pen_loading(self):
        """Adult 150mg: Sensoready Pen + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Sensoready Pen (1x150 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.patient_type.value == "Adult"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3"
        # Loading = 4 doses × 1 unit = 4
        assert rx.quantity.value == "4"
        # Loading doses have refills = "0" (as per current implementation)
        assert rx.refills.value == "0"

    def test_adult_150mg_sensoready_pen_maintenance(self):
        """Adult 150mg: Sensoready Pen + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Sensoready Pen (1x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        # Maintenance = 1 dose × 1 unit = 1 (for 28 days supply)
        assert rx.quantity.value == "1"
        assert rx.refills.value == "12 or 0"

    def test_adult_150mg_prefilled_syringe_loading(self):
        """Adult 150mg: Prefilled Syringe + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "syringe",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Prefilled Syringe (1x150 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3"
        assert rx.quantity.value == "4"
        assert rx.refills.value == "0"

    def test_adult_150mg_prefilled_syringe_maintenance(self):
        """Adult 150mg: Prefilled Syringe + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "syringe",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Prefilled Syringe (1x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        assert rx.quantity.value == "1"
        assert rx.refills.value == "12 or 0"


# ============================================================================
# ADULT 300mg SECTION TESTS
# ============================================================================

class TestAdult300mgCombinations:
    """Test all checkbox combinations for Adult COSENTYX 300mg section."""
    
    def test_adult_300mg_unoready_pen_loading(self):
        """Adult 300mg: UnoReady Pen + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "unoready_pen",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "UnoReady Pen (1x300 mg/2 mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.sig.value == "Inject 300 mg subcutaneously on Weeks 0, 1, 2, 3"
        assert rx.quantity.value == "4"
        assert rx.refills.value == "0"

    def test_adult_300mg_unoready_pen_maintenance(self):
        """Adult 300mg: UnoReady Pen + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "unoready_pen",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "UnoReady Pen (1x300 mg/2 mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        assert rx.quantity.value == "1"
        assert rx.refills.value == "12 or 0"

    def test_adult_300mg_unoready_pen_maintenance_increase(self):
        """Adult 300mg: UnoReady Pen + Maintenance Increase."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "unoready_pen",
            "dose_type": "maintenance_increase",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "UnoReady Pen (1x300 mg/2 mL)"
        assert rx.dose_type.value == "Maintenance Increase"
        assert "every 2 weeks" in rx.sig.value
        assert rx.quantity.value == "2"
        assert rx.refills.value == "12 or 0"

    def test_adult_300mg_sensoready_pen_loading(self):
        """Adult 300mg: Sensoready Pen (2x150mg/mL) + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "Sensoready Pen (2x150 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.sig.value == "Inject 300 mg subcutaneously on Weeks 0, 1, 2, 3"
        assert rx.quantity.value == "8"
        assert rx.refills.value == "0"

    def test_adult_300mg_sensoready_pen_maintenance(self):
        """Adult 300mg: Sensoready Pen (2x150mg/mL) + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "Sensoready Pen (2x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        assert rx.quantity.value == "2"
        assert rx.refills.value == "12 or 0"

    def test_adult_300mg_sensoready_pen_maintenance_increase(self):
        """Adult 300mg: Sensoready Pen (2x150mg/mL) + Maintenance Increase."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "maintenance_increase",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "Sensoready Pen (2x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance Increase"
        assert "every 2 weeks" in rx.sig.value
        assert rx.quantity.value == "4"
        assert rx.refills.value == "12 or 0"

    def test_adult_300mg_prefilled_syringe_loading(self):
        """Adult 300mg: Prefilled Syringe (2x150mg/mL) + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "syringe",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "Prefilled Syringe (2x150 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.sig.value == "Inject 300 mg subcutaneously on Weeks 0, 1, 2, 3"
        assert rx.quantity.value == "8"
        assert rx.refills.value == "0"

    def test_adult_300mg_prefilled_syringe_maintenance(self):
        """Adult 300mg: Prefilled Syringe (2x150mg/mL) + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "syringe",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "Prefilled Syringe (2x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 300 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        assert rx.quantity.value == "2"
        assert rx.refills.value == "12 or 0"

    def test_adult_300mg_prefilled_syringe_maintenance_increase(self):
        """Adult 300mg: Prefilled Syringe (2x150mg/mL) + Maintenance Increase."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "syringe",
            "dose_type": "maintenance_increase",
        })
        
        assert rx.dosage.value == "300mg"
        assert rx.form.value == "Prefilled Syringe (2x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance Increase"
        assert "every 2 weeks" in rx.sig.value
        assert rx.quantity.value == "4"
        assert rx.refills.value == "12 or 0"


# ============================================================================
# PEDIATRIC 75mg SECTION TESTS
# ============================================================================

class TestPediatric75mgCombinations:
    """Test all checkbox combinations for Pediatric COSENTYX 75mg section."""
    
    def test_pediatric_75mg_prefilled_syringe_loading(self):
        """Pediatric 75mg (wt <50kg): Prefilled Syringe + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "75mg",
            "patient_type": "pediatric",
            "form": "syringe",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "75mg"
        assert rx.form.value == "Prefilled Syringe (1x75 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.patient_type.value == "Pediatric"
        assert rx.sig.value == "Inject 75 mg subcutaneously on Weeks 0, 1, 2, 3"
        assert rx.quantity.value == "4"
        assert rx.refills.value == "0"

    def test_pediatric_75mg_prefilled_syringe_maintenance(self):
        """Pediatric 75mg (wt <50kg): Prefilled Syringe + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "75mg",
            "patient_type": "pediatric",
            "form": "syringe",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "75mg"
        assert rx.form.value == "Prefilled Syringe (1x75 mg/mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 75 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        assert rx.quantity.value == "1"
        assert rx.refills.value == "12 or 0"


# ============================================================================
# PEDIATRIC 150mg SECTION TESTS
# ============================================================================

class TestPediatric150mgCombinations:
    """Test all checkbox combinations for Pediatric COSENTYX 150mg section."""
    
    def test_pediatric_150mg_sensoready_pen_loading(self):
        """Pediatric 150mg (wt ≥50kg): Sensoready Pen + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "pediatric",
            "form": "sensoready_pen",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Sensoready Pen (1x150 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.patient_type.value == "Pediatric"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3"
        assert rx.quantity.value == "4"
        assert rx.refills.value == "0"

    def test_pediatric_150mg_sensoready_pen_maintenance(self):
        """Pediatric 150mg (wt ≥50kg): Sensoready Pen + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "pediatric",
            "form": "sensoready_pen",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Sensoready Pen (1x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        assert rx.quantity.value == "1"
        assert rx.refills.value == "12 or 0"

    def test_pediatric_150mg_prefilled_syringe_loading(self):
        """Pediatric 150mg (wt ≥50kg): Prefilled Syringe + Loading Dose."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "pediatric",
            "form": "syringe",
            "dose_type": "loading",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Prefilled Syringe (1x150 mg/mL)"
        assert rx.dose_type.value == "Loading"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3"
        assert rx.quantity.value == "4"
        assert rx.refills.value == "0"

    def test_pediatric_150mg_prefilled_syringe_maintenance(self):
        """Pediatric 150mg (wt ≥50kg): Prefilled Syringe + Maintenance."""
        extractor = PrescriptionExtractor()
        rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "pediatric",
            "form": "syringe",
            "dose_type": "maintenance",
        })
        
        assert rx.dosage.value == "150mg"
        assert rx.form.value == "Prefilled Syringe (1x150 mg/mL)"
        assert rx.dose_type.value == "Maintenance"
        assert rx.sig.value == "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter"
        assert rx.quantity.value == "1"
        assert rx.refills.value == "12 or 0"


# ============================================================================
# MULTI-PRESCRIPTION COMBINATION TESTS
# ============================================================================

class TestMultiplePrescriptionCombinations:
    """Test scenarios with multiple prescriptions selected."""
    
    def test_both_loading_and_maintenance_adult_150mg(self):
        """Adult 150mg: Both Loading and Maintenance selected for same device."""
        extractor = PrescriptionExtractor()
        
        # This should create 2 separate prescriptions
        prescriptions = _build_prescriptions(
            extractor,
            "adult",
            "150mg",
            devices=["sensoready_pen"],
            dosings=["loading", "maintenance"]
        )
        
        assert len(prescriptions) == 2
        loading_rx = next(rx for rx in prescriptions if rx.dose_type.value == "Loading")
        maintenance_rx = next(rx for rx in prescriptions if rx.dose_type.value == "Maintenance")
        
        assert loading_rx.quantity.value == "4"
        assert loading_rx.refills.value == "0"
        assert maintenance_rx.quantity.value == "1"
        assert maintenance_rx.refills.value == "12 or 0"

    def test_multiple_devices_same_dosing_adult_300mg(self):
        """Adult 300mg: Multiple devices with same dosing type."""
        extractor = PrescriptionExtractor()
        
        # UnoReady Pen + Sensoready Pen both with Maintenance
        prescriptions = _build_prescriptions(
            extractor,
            "adult",
            "300mg",
            devices=["unoready_pen", "sensoready_pen"],
            dosings=["maintenance"]
        )
        
        assert len(prescriptions) == 2
        uno_rx = next(rx for rx in prescriptions if "UnoReady" in rx.form.value)
        senso_rx = next(rx for rx in prescriptions if "Sensoready" in rx.form.value)
        
        # Different quantities for different forms
        assert uno_rx.quantity.value == "1"  # UnoReady is single dose
        assert senso_rx.quantity.value == "2"  # Sensoready is 2x150mg

    def test_cross_section_adult_and_pediatric(self):
        """Multiple prescriptions across Adult and Pediatric sections."""
        extractor = PrescriptionExtractor()
        
        # Adult 150mg Loading + Pediatric 75mg Maintenance
        adult_rx = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "loading",
        })
        
        pediatric_rx = extractor._create_prescription({
            "dosage": "75mg",
            "patient_type": "pediatric",
            "form": "syringe",
            "dose_type": "maintenance",
        })
        
        assert adult_rx.patient_type.value == "Adult"
        assert pediatric_rx.patient_type.value == "Pediatric"
        assert adult_rx.dosage.value == "150mg"
        assert pediatric_rx.dosage.value == "75mg"


# ============================================================================
# EDGE CASE AND VALIDATION TESTS
# ============================================================================

class TestEdgeCasesAndValidation:
    """Test edge cases and validation scenarios."""
    
    def test_all_adult_150mg_combinations_count(self):
        """Verify total combination count for Adult 150mg."""
        extractor = PrescriptionExtractor()
        
        adult_150 = _build_prescriptions(
            extractor,
            "adult",
            "150mg",
            devices=["sensoready_pen", "syringe"],
            dosings=["loading", "maintenance"],
        )
        
        # 2 devices × 2 dosings = 4 combinations
        assert len(adult_150) == 4

    def test_all_adult_300mg_combinations_count(self):
        """Verify total combination count for Adult 300mg."""
        extractor = PrescriptionExtractor()
        
        adult_300 = _build_prescriptions(
            extractor,
            "adult",
            "300mg",
            devices=["unoready_pen", "sensoready_pen", "syringe"],
            dosings=["loading", "maintenance", "maintenance_increase"],
        )
        
        # 3 devices × 3 dosings = 9 combinations
        assert len(adult_300) == 9

    def test_all_pediatric_75mg_combinations_count(self):
        """Verify total combination count for Pediatric 75mg."""
        extractor = PrescriptionExtractor()
        
        ped_75 = _build_prescriptions(
            extractor,
            "pediatric",
            "75mg",
            devices=["syringe"],
            dosings=["loading", "maintenance"],
        )
        
        # 1 device × 2 dosings = 2 combinations
        assert len(ped_75) == 2

    def test_all_pediatric_150mg_combinations_count(self):
        """Verify total combination count for Pediatric 150mg."""
        extractor = PrescriptionExtractor()
        
        ped_150 = _build_prescriptions(
            extractor,
            "pediatric",
            "150mg",
            devices=["sensoready_pen", "syringe"],
            dosings=["loading", "maintenance"],
        )
        
        # 2 devices × 2 dosings = 4 combinations
        assert len(ped_150) == 4

    def test_form_display_includes_strength_150mg(self):
        """Verify form display format includes strength for 150mg."""
        extractor = PrescriptionExtractor()
        
        rx_pen = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "loading",
        })
        assert rx_pen.form.value == "Sensoready Pen (1x150 mg/mL)"
        
        rx_syringe = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "syringe",
            "dose_type": "maintenance",
        })
        assert rx_syringe.form.value == "Prefilled Syringe (1x150 mg/mL)"

    def test_form_display_includes_strength_300mg(self):
        """Verify form display format includes strength for 300mg."""
        extractor = PrescriptionExtractor()
        
        rx_uno = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "unoready_pen",
            "dose_type": "loading",
        })
        assert rx_uno.form.value == "UnoReady Pen (1x300 mg/2 mL)"
        
        rx_senso = extractor._create_prescription({
            "dosage": "300mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "loading",
        })
        assert rx_senso.form.value == "Sensoready Pen (2x150 mg/mL)"

    def test_form_display_includes_strength_75mg(self):
        """Verify form display format includes strength for 75mg."""
        extractor = PrescriptionExtractor()
        
        rx_75 = extractor._create_prescription({
            "dosage": "75mg",
            "patient_type": "pediatric",
            "form": "syringe",
            "dose_type": "loading",
        })
        assert rx_75.form.value == "Prefilled Syringe (1x75 mg/mL)"

    def test_prescription_signature_uniqueness(self):
        """Verify each prescription has a unique signature."""
        extractor = PrescriptionExtractor()
        
        rx1 = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "loading",
        })
        
        rx2 = extractor._create_prescription({
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "sensoready_pen",
            "dose_type": "maintenance",
        })
        
        # Same device but different dose type = different signatures
        assert rx1.get_signature() != rx2.get_signature()

    def test_refills_na_for_loading_dose(self):
        """Verify refills are 0 for all loading doses."""
        extractor = PrescriptionExtractor()
        
        test_cases = [
            {"dosage": "150mg", "patient_type": "adult", "form": "sensoready_pen"},
            {"dosage": "300mg", "patient_type": "adult", "form": "unoready_pen"},
            {"dosage": "75mg", "patient_type": "pediatric", "form": "syringe"},
            {"dosage": "150mg", "patient_type": "pediatric", "form": "syringe"},
        ]
        
        for case in test_cases:
            case["dose_type"] = "loading"
            rx = extractor._create_prescription(case)
            assert rx.refills.value == "0", f"Failed for {case}"

    def test_refills_12_or_0_for_maintenance(self):
        """Verify refills are '12 or 0' for all maintenance doses."""
        extractor = PrescriptionExtractor()
        
        test_cases = [
            {"dosage": "150mg", "patient_type": "adult", "form": "sensoready_pen"},
            {"dosage": "300mg", "patient_type": "adult", "form": "unoready_pen"},
            {"dosage": "75mg", "patient_type": "pediatric", "form": "syringe"},
            {"dosage": "150mg", "patient_type": "pediatric", "form": "syringe"},
        ]
        
        for case in test_cases:
            case["dose_type"] = "maintenance"
            rx = extractor._create_prescription(case)
            assert rx.refills.value == "12 or 0", f"Failed for {case}"


# ============================================================================
# PARAMETRIZED COMPREHENSIVE TESTS
# ============================================================================

@pytest.mark.parametrize("dosage,patient_type,form,dose_type,expected_quantity,expected_refills", [
    # Adult 150mg combinations (loading=4x1, maintenance=1x1)
    ("150mg", "adult", "sensoready_pen", "loading", "4", "0"),
    ("150mg", "adult", "sensoready_pen", "maintenance", "1", "12 or 0"),
    ("150mg", "adult", "syringe", "loading", "4", "0"),
    ("150mg", "adult", "syringe", "maintenance", "1", "12 or 0"),
    
    # Adult 300mg combinations (loading=4x units, maintenance=1x units, increase=2x units)
    # UnoReady: 1 unit per dose (single 300mg pen)
    ("300mg", "adult", "unoready_pen", "loading", "4", "0"),
    ("300mg", "adult", "unoready_pen", "maintenance", "1", "12 or 0"),
    ("300mg", "adult", "unoready_pen", "maintenance_increase", "2", "12 or 0"),
    # Sensoready/Syringe: 2 units per dose (2x150mg = 300mg)
    ("300mg", "adult", "sensoready_pen", "loading", "8", "0"),
    ("300mg", "adult", "sensoready_pen", "maintenance", "2", "12 or 0"),
    ("300mg", "adult", "sensoready_pen", "maintenance_increase", "4", "12 or 0"),
    ("300mg", "adult", "syringe", "loading", "8", "0"),
    ("300mg", "adult", "syringe", "maintenance", "2", "12 or 0"),
    ("300mg", "adult", "syringe", "maintenance_increase", "4", "12 or 0"),
    
    # Pediatric 75mg combinations (loading=4x1, maintenance=1x1)
    ("75mg", "pediatric", "syringe", "loading", "4", "0"),
    ("75mg", "pediatric", "syringe", "maintenance", "1", "12 or 0"),
    
    # Pediatric 150mg combinations (loading=4x1, maintenance=1x1)
    ("150mg", "pediatric", "sensoready_pen", "loading", "4", "0"),
    ("150mg", "pediatric", "sensoready_pen", "maintenance", "1", "12 or 0"),
    ("150mg", "pediatric", "syringe", "loading", "4", "0"),
    ("150mg", "pediatric", "syringe", "maintenance", "1", "12 or 0"),
])
def test_all_checkbox_combinations_quantities(dosage, patient_type, form, dose_type, expected_quantity, expected_refills):
    """Parametrized test for all possible checkbox combinations and their quantities.
    
    Quantities are calculated as: doses_per_28_days × units_per_dose
    - Loading: 4 doses (Weeks 0, 1, 2, 3)
    - Maintenance: 1 dose (every 4 weeks)
    - Maintenance Increase: 2 doses (every 2 weeks)
    
    Units per dose:
    - 150mg/75mg: 1 unit (single pen/syringe)
    - 300mg UnoReady: 1 unit (single 300mg pen)
    - 300mg Sensoready/Syringe: 2 units (2x150mg to make 300mg)
    
    Refills:
    - Loading: "0" (no refills for loading doses)
    - Maintenance/Maintenance Increase: "12 or 0" (12 refills or handwritten value)
    """
    extractor = PrescriptionExtractor()
    
    rx = extractor._create_prescription({
        "dosage": dosage,
        "patient_type": patient_type,
        "form": form,
        "dose_type": dose_type,
    })
    
    assert rx.dosage.value == dosage
    assert rx.patient_type.value.lower() == patient_type.lower()
    assert rx.quantity.value == expected_quantity, f"Expected quantity {expected_quantity}, got {rx.quantity.value}"
    assert rx.refills.value == expected_refills, f"Expected refills {expected_refills}, got {rx.refills.value}"
    assert rx.sig.value is not None and len(rx.sig.value) > 0
