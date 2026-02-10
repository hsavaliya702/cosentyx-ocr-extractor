# Install Poppler for PDF to Image Conversion

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Poppler Installation for PDF Conversion" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan

Write-Host "`nDownloading poppler..." -ForegroundColor Cyan
$url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
$output = "poppler.zip"

try {
    Invoke-WebRequest -Uri $url -OutFile $output
    Write-Host "✓ Downloaded poppler" -ForegroundColor Green
    
    Write-Host "`nExtracting..." -ForegroundColor Cyan
    Expand-Archive -Path $output -DestinationPath "." -Force
    
    Write-Host "✓ Extracted to: poppler-24.08.0\" -ForegroundColor Green
    
    # Add to PATH for this session
    $popplerPath = Join-Path (Get-Location) "poppler-24.08.0\Library\bin"
    $env:PATH = "$popplerPath;$env:PATH"
    
    Write-Host "`n✓ Added to PATH for this session" -ForegroundColor Green
    Write-Host "  Path: $popplerPath" -ForegroundColor Gray
    
    # Clean up
    Remove-Item $output
    
    Write-Host "`n" -NoNewline
    Write-Host "=" -ForegroundColor Green -NoNewline
    Write-Host ("=" * 79) -ForegroundColor Green
    Write-Host "✓ Poppler installed successfully!" -ForegroundColor Green
    Write-Host "=" -ForegroundColor Green -NoNewline
    Write-Host ("=" * 79) -ForegroundColor Green
    
    Write-Host "`nYou can now run:" -ForegroundColor Yellow
    Write-Host "  venv\Scripts\python.exe examples\usage_example.py" -ForegroundColor White
    
} catch {
    Write-Host "✗ Installation failed: $_" -ForegroundColor Red
    Write-Host "`nManual installation:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/" -ForegroundColor White
    Write-Host "2. Extract the ZIP file" -ForegroundColor White
    Write-Host "3. Add the 'Library\bin' folder to your PATH" -ForegroundColor White
}
