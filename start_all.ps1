# Powershell script to launch FastAPI Backend and Permanent Tunnel simultaneously

Write-Host "Starting AI Voice Banking Assistant Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Write-Host 'FastAPI Server Port 8000' -ForegroundColor Cyan; .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload }"

Write-Host "Starting Permanent Tunnel Server..." -ForegroundColor Green

# Check for local ngrok.exe or PATH ngrok
$ngrokPath = if (Test-Path ".\ngrok.exe") { ".\ngrok.exe" } elseif (Get-Command "ngrok" -ErrorAction SilentlyContinue) { "ngrok" } else { $null }

if ($ngrokPath) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Write-Host 'Ngrok https://rental-hardy-exerciser.ngrok-free.dev' -ForegroundColor Yellow; $ngrokPath http 8000 --domain=rental-hardy-exerciser.ngrok-free.dev }"
    Write-Host "Permanent Public URL: https://rental-hardy-exerciser.ngrok-free.dev/api/vapi/webhook" -ForegroundColor White
} else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Write-Host 'LocalTunnel https://shantanu-voice-bank.loca.lt' -ForegroundColor Yellow; npx localtunnel --port 8000 --subdomain shantanu-voice-bank }"
    Write-Host "Public URL: https://shantanu-voice-bank.loca.lt/api/vapi/webhook" -ForegroundColor White
}

Write-Host "Both servers launched successfully!" -ForegroundColor Green
