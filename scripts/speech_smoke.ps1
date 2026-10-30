$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory -Force -Path artifacts | Out-Null
Add-Type -AssemblyName System.Speech
$signbridgeVoice = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $signbridgeVoice.SetOutputToWaveFile((Join-Path (Get-Location) 'artifacts\speech-smoke.wav'))
    $signbridgeVoice.Speak('Hello friend. Thank you. Please help me. I need water.')
} finally {
    $signbridgeVoice.Dispose()
}
& '.\.venv\Scripts\python.exe' -c "from pathlib import Path; from text_to_sign.speech import transcribe; print(transcribe(Path('artifacts/speech-smoke.wav')))"
if ($LASTEXITCODE -ne 0) { throw 'Speech smoke test failed.' }
