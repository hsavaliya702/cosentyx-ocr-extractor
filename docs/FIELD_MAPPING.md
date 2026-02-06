# Field Mapping Guide

This guide documents how form fields are mapped from various naming conventions to standardized field names.

## Patient Information

### First Name
**Standardized Field**: `patient.first_name`

**Recognized Variations**:
- patient first name
- first name
- fname
- patient fname
- member first name
- member fname

**Example Extraction**:
```
Form: "Patient First Name: John"
Result: patient.first_name.value = "John"
```

### Last Name
**Standardized Field**: `patient.last_name`

**Recognized Variations**:
- patient last name
- last name
- lname
- patient lname
- member last name
- member lname

### Date of Birth
**Standardized Field**: `patient.dob`

**Recognized Variations**:
- date of birth
- dob
- birth date
- birthdate
- patient dob
- member dob
- date birth

**Input Formats Accepted**:
- MM/DD/YYYY (e.g., 01/15/1980)
- M/D/YY (e.g., 1/15/80)
- MM-DD-YYYY (e.g., 01-15-1980)
- YYYY-MM-DD (e.g., 1980-01-15)
- Month DD, YYYY (e.g., January 15, 1980)

**Output Format**: MM/DD/YYYY

### Gender
**Standardized Field**: `patient.gender`

**Recognized Variations**:
- sex
- gender
- patient gender
- patient sex
- member gender

**Input Values Accepted**:
- M, Male → "M"
- F, Female → "F"
- O, Other, X, U, Unknown → "Other"

**Output Format**: M / F / Other

### Phone Number
**Standardized Field**: `patient.phone`

**Recognized Variations**:
- phone
- telephone
- phone number
- patient phone
- member phone
- contact phone
- tel

**Input Formats Accepted**:
- 5551234567
- (555) 123-4567
- 555-123-4567
- 555.123.4567

**Output Format**: (555) 123-4567

### Email
**Standardized Field**: `patient.email`

**Recognized Variations**:
- email
- email address
- patient email
- member email
- e-mail
- e-mail address

**Validation**: Standard email regex

**Output Format**: Lowercase

## Prescriber Information

### First Name
**Standardized Field**: `prescriber.first_name`

**Recognized Variations**:
- prescriber first name
- physician first name
- doctor first name
- dr first name
- prescriber fname
- physician fname

### Last Name
**Standardized Field**: `prescriber.last_name`

**Recognized Variations**:
- prescriber last name
- physician last name
- doctor last name
- dr last name
- prescriber lname
- physician lname

### NPI
**Standardized Field**: `prescriber.npi`

**Recognized Variations**:
- npi
- npi number
- prescriber npi
- physician npi
- national provider identifier

**Input Formats Accepted**:
- 1234567890
- 123-456-7890
- 123 456 7890

**Output Format**: 10 digits (no formatting)

**Validation**: Must be exactly 10 numeric digits

### Address - Street
**Standardized Field**: `prescriber.address.street`

**Recognized Variations**:
- prescriber address
- physician address
- address
- street address
- street
- prescriber street
- office address

### Address - City
**Standardized Field**: `prescriber.address.city`

**Recognized Variations**:
- city
- prescriber city
- physician city
- office city

### Address - State
**Standardized Field**: `prescriber.address.state`

**Recognized Variations**:
- state
- prescriber state
- physician state
- office state

**Validation**: Must be valid 2-letter US state code

**Output Format**: Uppercase (e.g., MA, CA, NY)

### Address - ZIP
**Standardized Field**: `prescriber.address.zip`

**Recognized Variations**:
- zip
- zip code
- zipcode
- postal code
- prescriber zip
- physician zip

**Input Formats Accepted**:
- 5-digit: 02101
- 9-digit: 02101-1234 or 021011234

**Output Format**: 
- 5-digit: 02101
- 9-digit: 02101-1234

### Phone
**Standardized Field**: `prescriber.phone`

**Recognized Variations**:
- prescriber phone
- physician phone
- office phone
- phone
- prescriber telephone
- office telephone

**Format**: Same as patient phone

### Fax
**Standardized Field**: `prescriber.fax`

**Recognized Variations**:
- fax
- fax number
- prescriber fax
- physician fax
- office fax

**Format**: Same as patient phone

**Note**: Either phone OR fax is required (at least one)

## Prescription Information

The prescription section extracts ONE prescription per form based on checkbox selections. See [MULTIPLE_PRESCRIPTIONS.md](MULTIPLE_PRESCRIPTIONS.md) for detailed logic.

### Core Structure

Each prescription consists of:
- **Device Selection**: ONE device checkbox (Sensoready Pen, UnoReady Pen, or Prefilled Syringe)
- **Dosing Selection**: ONE dosing checkbox (Loading, Maintenance, or Maintenance Increase)

### Product
**Standardized Field**: `prescription.prescriptions[0].product`

**Expected Values**: 
- COSENTYX 150mg
- COSENTYX 300mg
- COSENTYX 75mg

**Source**: Derived from checkbox context (dosage detection)

### Dosage
**Standardized Field**: `prescription.prescriptions[0].dosage`

**Expected Values**: 
- 150mg (Adult or Pediatric ≥50kg)
- 300mg (Adult only)
- 75mg (Pediatric <50kg)

**Source**: Extracted from checkbox nearby text

### Form (Device)
**Standardized Field**: `prescription.prescriptions[0].form`

**Expected Values**:
- Sensoready Pen
- UnoReady Pen
- Prefilled Syringe

**Checkbox Detection**: Left side of form (left < 0.35)

### Dose Type
**Standardized Field**: `prescription.prescriptions[0].dose_type`

**Expected Values**:
- Loading (initial 4-week loading dose)
- Maintenance (ongoing maintenance dose)
- Maintenance Increase (increased frequency for HS only)

**Checkbox Detection**: Middle-right of form (left 0.35-0.70)

### Patient Type
**Standardized Field**: `prescription.prescriptions[0].patient_type`

**Expected Values**:
- Adult
- Pediatric

**Source**: Derived from dosage (75mg = always Pediatric, 300mg = always Adult, 150mg = depends on context)

### Quantity
**Standardized Field**: `prescription.prescriptions[0].quantity`

**Auto-Populated Values**:
- Loading: "4" (4 weeks)
- Maintenance: "12" (12 doses for year)
- Maintenance Increase: "12" (every 2 weeks)

**Source**: "lookup" (from DOSING_INFO table)

### SIG (Directions)
**Standardized Field**: `prescription.prescriptions[0].sig`

**Auto-Populated Examples**:
- "Inject 150 mg subcutaneously on Weeks 0, 1, 2, 3" (Loading)
- "Inject 150 mg subcutaneously on Week 4, then every 4 weeks thereafter" (Maintenance)
- "Inject 300 mg subcutaneously every 2 weeks (For patients currently taking COSENTYX every 4 weeks as per label. Loading dose already completed.)" (Maintenance Increase)

**Source**: "lookup" (from DOSING_INFO table)

### Refills
**Standardized Field**: `prescription.prescriptions[0].refills`

**Expected Values**:
- "N/A" (Loading dose - no refills)
- "12 or 0" (Maintenance - form allows selection)
- "12 or 3", "12 or 5" (other refill options)

**Checkbox Detection**: Far right of form (left ≥ 0.70), matched to dosing row

**Source**: Extracted from form checkbox context or lookup default

### Validation Rules

**Valid Prescription Requirements**:
- Product: Must have value
- Dosage: Must be 75mg, 150mg, or 300mg
- Form: Must be Sensoready Pen, UnoReady Pen, or Prefilled Syringe
- Dose Type: Must be Loading, Maintenance, or Maintenance Increase
- Quantity: Must have value
- SIG: Must have value

**Mutual Exclusivity** (enforced by PDF form):
- Only ONE section active (Adult OR Pediatric)
- Within section: Only ONE dosage (150mg OR 300mg for Adult; 75mg OR 150mg for Pediatric)
- Within row: Only ONE device selected
- Within row: Only ONE dosing selected

See [MULTIPLE_PRESCRIPTIONS.md](MULTIPLE_PRESCRIPTIONS.md) for complete details.

## Attestation Information

### Prescriber Name
**Standardized Field**: `attestation.name`

**Recognized Variations**:
- prescriber signature
- signature name
- signed by
- prescriber name
- physician name
- attestation name

**Example**: "Dr. Jane Smith" or "Jane Smith, MD"

### Attestation Date
**Standardized Field**: `attestation.date`

**Recognized Variations**:
- signature date
- date signed
- attestation date
- sign date

**Format**: Same as patient DOB (MM/DD/YYYY)

### Signature Presence
**Standardized Field**: `attestation.signature_present`

**Detection**: Automatically detected by Textract SIGNATURE feature

**Output**: Boolean (true/false)

**Confidence**: 0.0-1.0 based on Textract signature detection

## Fuzzy Matching Rules

The system uses the following strategies to find fields:

1. **Exact Match**: Field name matches exactly
2. **Case-Insensitive Match**: Field name matches ignoring case
3. **Partial Match**: Field name contains search term or vice versa
4. **Fallback to Payload**: If not found in form, check payload data

## Field Confidence Scores

Confidence scores indicate the reliability of extracted data:

- **0.9-1.0**: High confidence (form extraction)
- **0.85-0.89**: Medium confidence (may trigger warning)
- **0.0-0.84**: Low confidence (may require manual review)
- **1.0**: Perfect confidence (payload data)

## Special Cases

### Missing Optional Fields
Optional fields (phone, email, preferred_language, fax) return `null` if not found and are still considered valid.

### Multiple Matches
If multiple fields match the same search term, the system uses the first match found.

### Conflicting Data
If both form and payload contain the same field:
- Payload data takes precedence
- Source is marked as "payload"
- Confidence is set to 1.0

### Date Parsing Failures
If a date cannot be parsed:
- Field is marked as invalid
- Original value is preserved
- Error message indicates the issue

### Phone Number Formatting
All phone numbers are standardized to (XXX) XXX-XXXX format regardless of input format.
