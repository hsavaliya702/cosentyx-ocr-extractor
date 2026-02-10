"""End-to-end validation of pipeline_output.json prescriptions."""

import json
from pathlib import Path


def _expected_quantity(dosage, form_value, dose_type):
    dose_type_lower = (dose_type or "").lower()
    if "loading" in dose_type_lower:
        doses_per_28_days = 4
    elif "maintenance increase" in dose_type_lower:
        doses_per_28_days = 2
    else:
        doses_per_28_days = 1

    units_per_dose = 1
    if dosage == "300mg":
        if "2x150" in (form_value or "").lower():
            units_per_dose = 2
        else:
            units_per_dose = 1

    return str(doses_per_28_days * units_per_dose)


def test_pipeline_output_json_prescriptions():
    output_path = Path(__file__).parent.parent / "examples" / "pipeline_output.json"
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload.get("document_type") == "cosentyx_start_form"
    prescriptions = payload.get("prescription", {}).get("prescriptions", [])
    assert len(prescriptions) > 0

    for rx in prescriptions:
        product = rx["product"]["value"]
        dosage = rx["dosage"]["value"]
        form = rx["form"]["value"]
        dose_type = rx["dose_type"]["value"]
        quantity = rx["quantity"]["value"]

        assert product and dosage and form and dose_type and quantity
        assert product.endswith(dosage)

        expected = _expected_quantity(dosage, form, dose_type)
        assert quantity == expected
