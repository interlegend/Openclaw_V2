# OpenClaw Windows Launcher (Portable Version)
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# Resolve path to the .venv one level up
$VenvPython = Join-Path (Split-Path -Parent $PSScriptRoot) ".venv\Scripts\python.exe"

Write-Host "🐾 Starting OpenClaw..." -ForegroundColor Cyan

if (Test-Path $VenvPython) {
    Write-Host "✅ Environment: Virtual (.venv)" -ForegroundColor Green
    & $VenvPython bot.py
} else {
    Write-Host "⚠️ Virtual environment not found. Trying global python..." -ForegroundColor Yellow
    python bot.py
}

Write-Host "`n⚠️ OpenClaw has stopped." -ForegroundColor Yellow
Pause
