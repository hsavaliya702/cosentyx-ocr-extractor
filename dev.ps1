# Cosentyx OCR Extractor - Development Helper
# This script makes it easy to run commands with the virtual environment

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Cosentyx OCR Extractor - Development Helper" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$venvPython = "venv\Scripts\python.exe"

function Show-Menu {
    Write-Host "`nAvailable Commands:" -ForegroundColor Green
    Write-Host "  1. Run All Tests" -ForegroundColor White
    Write-Host "  2. Run Tests with Coverage" -ForegroundColor White
    Write-Host "  3. Run Example (requires AWS credentials)" -ForegroundColor White
    Write-Host "  4. Verify Setup" -ForegroundColor White
    Write-Host "  5. Format Code (black + isort)" -ForegroundColor White
    Write-Host "  6. Type Check (mypy)" -ForegroundColor White
    Write-Host "  7. Check .env Configuration" -ForegroundColor White
    Write-Host "  8. Open Python REPL" -ForegroundColor White
    Write-Host "  0. Exit" -ForegroundColor Gray
    Write-Host ""
}

function Run-Tests {
    Write-Host "`nRunning tests..." -ForegroundColor Cyan
    & $venvPython -m pytest tests/ -v
}

function Run-TestsWithCoverage {
    Write-Host "`nRunning tests with coverage..." -ForegroundColor Cyan
    & $venvPython -m pytest tests/ --cov=src --cov-report=term-missing
}

function Run-Example {
    Write-Host "`nRunning example..." -ForegroundColor Cyan
    Write-Host "[WARN] This requires AWS credentials in .env file" -ForegroundColor Yellow
    & $venvPython examples\usage_example.py
}

function Verify-Setup {
    Write-Host "`nVerifying setup..." -ForegroundColor Cyan
    & $venvPython test_setup.py
}

function Format-Code {
    Write-Host "`nFormatting code..." -ForegroundColor Cyan
    Write-Host "Running black..." -ForegroundColor Gray
    & $venvPython -m black src/ tests/
    Write-Host "`nRunning isort..." -ForegroundColor Gray
    & $venvPython -m isort src/ tests/
    Write-Host "`n[OK] Code formatted!" -ForegroundColor Green
}

function Run-TypeCheck {
    Write-Host "`nRunning type check..." -ForegroundColor Cyan
    & $venvPython -m mypy src/
}

function Check-EnvFile {
    Write-Host "`nChecking .env configuration..." -ForegroundColor Cyan
    if (Test-Path .env) {
        Write-Host "[OK] .env file exists" -ForegroundColor Green
        $content = Get-Content .env -Raw
        
        if ($content -match "AWS_ACCESS_KEY_ID=your_access_key") {
            Write-Host "[WARN] AWS_ACCESS_KEY_ID needs to be updated" -ForegroundColor Yellow
        } else {
            Write-Host "[OK] AWS_ACCESS_KEY_ID appears to be set" -ForegroundColor Green
        }
        
        if ($content -match "AWS_SECRET_ACCESS_KEY=your_secret_key") {
            Write-Host "[WARN] AWS_SECRET_ACCESS_KEY needs to be updated" -ForegroundColor Yellow
        } else {
            Write-Host "[OK] AWS_SECRET_ACCESS_KEY appears to be set" -ForegroundColor Green
        }
        
        Write-Host "`nTo edit .env file, run: notepad .env" -ForegroundColor Gray
    } else {
        Write-Host "[ERROR] .env file not found" -ForegroundColor Red
        Write-Host "Run: Copy-Item .env.example .env" -ForegroundColor Yellow
    }
}

function Open-REPL {
    Write-Host "`nOpening Python REPL..." -ForegroundColor Cyan
    Write-Host "Tip: Import with: from src.processor import CosentyxFormProcessor" -ForegroundColor Gray
    & $venvPython
}

# Main menu loop
while ($true) {
    Show-Menu
    $choice = Read-Host "Select an option"
    
    switch ($choice) {
        "1" { Run-Tests }
        "2" { Run-TestsWithCoverage }
        "3" { Run-Example }
        "4" { Verify-Setup }
        "5" { Format-Code }
        "6" { Run-TypeCheck }
        "7" { Check-EnvFile }
        "8" { Open-REPL; break }
        "0" { 
            Write-Host "`nGoodbye!" -ForegroundColor Cyan
            break 
        }
        default { 
            Write-Host "`nInvalid option. Please try again." -ForegroundColor Red 
        }
    }
    
    if ($choice -ne "8" -and $choice -ne "0") {
        Write-Host "`nPress Enter to continue..." -ForegroundColor Gray
        Read-Host
    }
}
