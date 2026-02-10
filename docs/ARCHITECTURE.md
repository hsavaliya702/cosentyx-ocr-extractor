# Architecture Documentation

## System Overview

The Cosentyx OCR Extractor is a production-ready document processing system that combines AWS Textract for optical character recognition with AWS Bedrock (Claude 3.5 Sonnet) for intelligent document classification and validation.

## Components

### 1. OCR Layer (AWS Textract)

**Purpose**: Extract raw text, form fields, tables, and signatures from PDF documents.

**Key Classes**:
- `TextractClient`: Handles AWS Textract API calls
- `TextractParser`: Parses and structures Textract responses

**Features**:
- Form field extraction (key-value pairs)
- Table detection and parsing
- Checkbox/selection element detection
- Signature presence detection
- Confidence scoring for all extracted elements

### 2. Classification Layer (AWS Bedrock)

**Purpose**: Classify documents to ensure they are valid Cosentyx/EMA Start Forms.

**Key Classes**:
- `BedrockClassifier`: Uses Claude 3.5 Sonnet for classification

**Document Types**:
- `ema_start_form` - EMA Start Form (ACCEPTED)
- `cosentyx_start_form` - Cosentyx Start Form (ACCEPTED)
- `cover_letter` - Cover letter (REJECTED)
- `benefits_statement` - Benefits statement (REJECTED)
- `clinical_info` - Clinical information (REJECTED)
- `other` - Unknown document type (REJECTED)

### 3. Extraction Layer

**Purpose**: Extract structured data from OCR results into typed data models.

**Key Classes**:
- `BaseExtractor`: Abstract base class for all extractors
- `PatientExtractor`: Extracts patient information
- `PrescriberExtractor`: Extracts prescriber information
- `PrescriptionExtractor`: Extracts prescription details
- `AttestationExtractor`: Extracts attestation/signature information

**Field Mapping Strategy**:
- Multiple field name variations per field (fuzzy matching)
- Case-insensitive matching
- Partial matching for field names
- Fallback to payload data if not found in form

### 4. Validation Layer

**Purpose**: Validate and format extracted data.

**Key Classes**:
- `FieldValidators`: Field-level validation (dates, phones, NPI, etc.)
- `BedrockValidator`: LLM-based intelligent validation (optional)
- `BusinessRules`: Business logic validation and routing

**Validation Types**:
- Format validation (phone, email, date, ZIP, etc.)
- Data type validation
- Required field validation
- Cross-field validation
- Business rule validation

### 5. Data Models (Pydantic)

**Purpose**: Type-safe data structures with built-in validation.

**Key Models**:
- `PatientInfo`: Patient demographic information
- `PrescriberInfo`: Prescriber and practice information
- `PrescriptionInfo`: Medication details
- `AttestationInfo`: Signature and attestation
- `ExtractionResult`: Complete extraction result with routing

**Field Structure**:
Each field includes:
- `value`: The extracted/validated value
- `source`: Where the value came from ("form" or "payload")
- `confidence`: OCR confidence score (0.0-1.0)
- `validated`: Whether the field passed validation
- `original_value`: Original value before formatting (if changed)

### 6. Main Processor

**Purpose**: Orchestrate the complete processing pipeline.

**Key Class**:
- `CosentyxFormProcessor`: Main entry point

**Pipeline Steps**:
1. OCR with AWS Textract
2. Document classification with Bedrock
3. Field extraction (patient, prescriber, prescription, attestation)
4. Field validation
5. Business rules application
6. Routing decision
7. Result packaging

### 7. Lambda Handler

**Purpose**: AWS Lambda entry point for serverless deployment.

**Event Types Supported**:
- S3 event (automatic processing on upload)
- Direct API invocation (base64-encoded document)

## Data Flow

```
┌──────────────┐
│ PDF Document │
└──────┬───────┘
       │
       v
┌──────────────────────────────────────────┐
│ Step 1: AWS Textract OCR                 │
│ - Extract text blocks                    │
│ - Extract form key-value pairs           │
│ - Detect tables                          │
│ - Detect signatures                      │
└──────────────┬───────────────────────────┘
               │
               v
┌──────────────────────────────────────────┐
│ Step 2: Document Classification          │
│ - Classify with Claude 3.5 Sonnet        │
│ - Determine document type                │
│ - Calculate confidence                   │
└──────────────┬───────────────────────────┘
               │
               v
┌──────────────────────────────────────────┐
│ Step 3: Field Extraction                 │
│ - PatientExtractor → PatientInfo         │
│ - PrescriberExtractor → PrescriberInfo   │
│ - PrescriptionExtractor → PrescriptionInfo│
│ - AttestationExtractor → AttestationInfo │
└──────────────┬───────────────────────────┘
               │
               v
┌──────────────────────────────────────────┐
│ Step 4: Field Validation                 │
│ - Format validation (dates, phones, etc) │
│ - Required field validation              │
│ - Optional: Bedrock-based validation     │
└──────────────┬───────────────────────────┘
               │
               v
┌──────────────────────────────────────────┐
│ Step 5: Business Rules                   │
│ - Check document type validity           │
│ - Apply routing logic                    │
│ - Check for duplicates (optional)        │
│ - Generate warnings                      │
└──────────────┬───────────────────────────┘
               │
               v
┌──────────────────────────────────────────┐
│ Step 6: Result Packaging                 │
│ - Create ExtractionResult                │
│ - Include metadata (time, cost)          │
│ - Routing decision                       │
│ - Validation errors/warnings             │
└──────────────┬───────────────────────────┘
               │
               v
┌──────────────┐
│ JSON Output  │
└──────────────┘
```

## Routing Logic

The system implements intelligent routing based on validation results:

### Complete Profile Creation
**Conditions**: All fields valid (patient, prescriber, prescription, attestation)
**Action**: Create full profile in system
**Manual Review**: No

### Patient-Only Profile
**Conditions**: Patient valid, but prescriber or prescription invalid
**Action**: Create patient profile only
**Manual Review**: Yes (missing prescriber/prescription data)

### Manual Review
**Conditions**: 
- Invalid document type
- Missing critical patient data
- Processing errors
**Action**: Route to manual review queue
**Manual Review**: Yes

## Error Handling

### Graceful Degradation
- If Textract fails → return error result
- If Bedrock classification fails → default to "other"
- If field validation fails → mark as invalid but continue processing
- If Bedrock validation fails → fall back to basic validation

### Logging
- All processing steps are logged
- Errors include full stack traces
- Performance metrics tracked
- Cost estimates calculated

## Performance Optimization

### Caching
- Settings loaded once and cached
- AWS clients reused across invocations

### Parallel Processing
- Field extractors can run independently
- Validation can be parallelized

### Cost Optimization
- Textract called once per document
- Bedrock calls minimized (classification + optional validation)
- No unnecessary API calls

## Scalability

### Horizontal Scaling
- Stateless design
- Each document processed independently
- No shared state between invocations

### AWS Lambda
- Auto-scales with load
- Pay per invocation
- Suitable for variable workloads

### ECS/Fargate
- Container-based deployment
- Suitable for high-volume, consistent workloads
- More control over resources

## Security Considerations

### Data Privacy
- No data stored permanently (stateless)
- AWS credentials managed via environment variables
- No sensitive data logged

### AWS Permissions Required
- `textract:AnalyzeDocument`
- `bedrock:InvokeModel`
- `s3:GetObject`, `s3:PutObject` (if using S3)
- `dynamodb:PutItem`, `dynamodb:GetItem` (if using DynamoDB)

## Monitoring

### Metrics to Track
- Processing time per document
- Textract API latency
- Bedrock API latency
- Validation success rate
- Manual review rate
- Error rate

### Logging Levels
- `INFO`: Normal processing flow
- `WARNING`: Low confidence fields, potential issues
- `ERROR`: Processing failures, API errors
- `DEBUG`: Detailed debugging information

## Future Enhancements

### Potential Improvements
1. Batch processing for multiple documents
2. Async processing with webhooks
3. Machine learning model for field correction
4. Historical data analysis for accuracy improvement
5. A/B testing framework for different extraction strategies
6. Real-time confidence threshold adjustment
7. Integration with downstream systems (EMR, pharmacy systems)
