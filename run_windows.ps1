Write-Host "VisionGuard AI - Windows setup" -ForegroundColor Cyan

py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python 3.12 was not found. Install Python 3.12 first." -ForegroundColor Red
    exit 1
}

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host ""
Write-Host "Starting server..." -ForegroundColor Green
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
