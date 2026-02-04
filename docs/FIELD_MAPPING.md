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

### Product Name
**Standardized Field**: `prescription.product`

**Recognized Variations**:
- product
- drug
- medication
- drug name
- product name
- cosentyx
- medicine

**Expected Values**: Cosentyx, Cosentyx Pen, Cosentyx Syringe

### Dosage
**Standardized Field**: `prescription.dosage`

**Recognized Variations**:
- dosage
- dose
- strength
- drug strength
- product strength

**Expected Values**: 150mg, 300mg

### Quantity
**Standardized Field**: `prescription.quantity`

**Recognized Variations**:
- quantity
- qty
- amount
- number of units
- units

**Expected Values**: Numeric (1, 2, 3, etc.)

### SIG (Directions)
**Standardized Field**: `prescription.sig`

**Recognized Variations**:
- sig
- directions
- instructions
- directions for use
- how to use
- administration

**Example Values**:
- "Inject 1 pen weekly"
- "Inject 300mg subcutaneously once weekly"
- "Use as directed"

### Refills
**Standardized Field**: `prescription.refills`

**Recognized Variations**:
- refills
- number of refills
- refill
- rx refills

**Expected Values**: Numeric (0, 1, 2, 3, etc.)

**Default**: "0" if not specified

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
