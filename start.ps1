$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
try {
    $signbridgeHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
    if ($signbridgeHealth.application -eq 'SignBridge') {
        Write-Host 'SignBridge is already running at http://127.0.0.1:8000'
        return
    }
} catch { }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& '.\.venv\Scripts\python.exe' scripts/setup_project.py
if ($LASTEXITCODE -ne 0) { throw 'Setup failed. See the download or dependency error above, then retry.' }
Write-Host 'Open http://127.0.0.1:8000. Press Ctrl+C here to stop the server.'
& '.\.venv\Scripts\python.exe' -m uvicorn text_to_sign.app:app --host 127.0.0.1 --port 8000
