# Quick Start Guide

## ✅ Setup Complete!

Your Cosentyx OCR Extractor is now ready to use.

## 📋 What Was Installed

- Python virtual environment (`venv/`)
- All required dependencies (boto3, pydantic, pytest, etc.)
- `.env` configuration file
- Sample form for testing (EMA-Start-Form_1.pdf)

## 🔑 Before Running with Real AWS

**You need AWS credentials to process actual documents:**

1. Edit `.env` file and add your AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=your_actual_access_key
   AWS_SECRET_ACCESS_KEY=your_actual_secret_key
   ```

2. **Required AWS Permissions:**
   - `textract:AnalyzeDocument` - For OCR processing
   - `bedrock:InvokeModel` - For AI classification/validation
   - `s3:GetObject`, `s3:PutObject` - Optional, for S3 integration

3. **Get AWS Credentials:**
   - Log in to [AWS Console](https://console.aws.amazon.com)
   - Navigate to: IAM → Users → Your User → Security Credentials
   - Click "Create Access Key"

## 🚀 How to Run

### Option 1: Run Tests (No AWS credentials needed)
```powershell
venv\Scripts\python.exe -m pytest tests/ -v
```

### Option 2: Run Example (Requires AWS credentials)
```powershell
venv\Scripts\python.exe examples\usage_example.py
```

### Option 3: Use Python API
```python
from src.processor import CosentyxFormProcessor

# Initialize processor
processor = CosentyxFormProcessor()

# Process a document
with open("examples/sample_forms/EMA-Start-Form_1.pdf", "rb") as f:
    document_bytes = f.read()

result = processor.process_document(document_bytes)

# Access results
print(f"Document Type: {result.document_type}")
print(f"Routing Action: {result.routing.action}")
print(f"Patient: {result.patient.first_name.value}")
```

## 🔧 Development Commands

### Activate Virtual Environment
```powershell
# PowerShell (if execution policy allows)
.\venv\Scripts\Activate.ps1

# Or use direct path to Python
venv\Scripts\python.exe <script.py>
```

### Run Tests
```powershell
# All tests
venv\Scripts\python.exe -m pytest tests/

# With coverage
venv\Scripts\python.exe -m pytest tests/ --cov=src

# Specific test file
venv\Scripts\python.exe -m pytest tests/test_validators.py -v
```

### Format Code
```powershell
venv\Scripts\python.exe -m black src/ tests/
venv\Scripts\python.exe -m isort src/ tests/
```

### Type Checking
```powershell
venv\Scripts\python.exe -m mypy src/
```

## 📁 Project Structure

```
cosentyx-ocr-extractor/
├── src/                        # Main source code
│   ├── processor.py           # Main orchestration (START HERE)
│   ├── lambda_handler.py      # AWS Lambda entry point
│   ├── ocr/                   # Textract integration
│   ├── classification/        # Document classification
│   ├── extraction/            # Field extractors
│   ├── validation/            # Validators & business rules
│   └── models/                # Pydantic data models
├── tests/                     # Test suite
├── examples/                  # Usage examples
├── docs/                      # Documentation
└── .env                       # Configuration (ADD CREDENTIALS)
```

## 📖 Documentation

- `docs/ARCHITECTURE.md` - System architecture details
- `docs/FIELD_MAPPING.md` - Field extraction patterns
- `docs/API_DOCUMENTATION.md` - API usage guide
- `docs/DEPLOYMENT.md` - AWS deployment instructions
- `.github/copilot-instructions.md` - AI agent guidelines

## 🔍 Testing Without AWS

The test suite uses mocked AWS services, so you can run tests without AWS credentials:

```powershell
venv\Scripts\python.exe -m pytest tests/ -v
```

All 31 tests should pass ✅

## ⚠️ Common Issues

### 1. PowerShell Script Execution Policy
If you can't activate the venv, use direct python path:
```powershell
venv\Scripts\python.exe script.py
```

### 2. AWS Credentials Not Found
Make sure you've updated `.env` with real AWS credentials before running examples.

### 3. Import Errors
Make sure you're using the virtual environment python:
```powershell
venv\Scripts\python.exe -c "import sys; print(sys.executable)"
```

## 🎯 Next Steps

1. ✅ **Setup Complete** - Project is ready!
2. ⏸️ **Add AWS Credentials** - Edit `.env` file
3. 🚀 **Run Example** - Try processing a sample form
4. 📝 **Read Docs** - Explore `docs/` folder
5. 🧪 **Run Tests** - Verify everything works

## 💡 Quick Tips

- Use `venv\Scripts\python.exe` prefix for all commands
- Tests don't need AWS credentials (mocked)
- Examples require real AWS credentials
- Check `.github/copilot-instructions.md` for development patterns
- Sample form is in `examples/sample_forms/`

## 📞 Need Help?

- Check `README.md` for detailed documentation
- Review `docs/ARCHITECTURE.md` for system design
- Run `venv\Scripts\python.exe test_setup.py` to verify setup
