# OpenClaw Windows Launcher (Portable Version)
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# 1. Try local venv first, then fall back to parent folder venv
$LocalVenv = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$ParentVenv = Join-Path (Split-Path -Parent $PSScriptRoot) ".venv\Scripts\python.exe"

if (Test-Path $LocalVenv) {
    $VenvPython = $LocalVenv
} elseif (Test-Path $ParentVenv) {
    $VenvPython = $ParentVenv
} else {
    $VenvPython = $null
}

Write-Host "🐾 Starting OpenClaw..." -ForegroundColor Cyan

if ($null -ne $VenvPython) {
    Write-Host "✅ Environment: Virtual ($VenvPython)" -ForegroundColor Green
    & $VenvPython bot.py
} else {
    Write-Host "⚠️ Virtual environment not found. Trying global python..." -ForegroundColor Yellow
    python bot.py
}

Write-Host "`n⚠️ OpenClaw has stopped." -ForegroundColor Yellow
Pause

