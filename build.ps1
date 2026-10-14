# Сборка AutoClicker.exe в папку dist\
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) {
    python -m venv .venv
}
.\.venv\Scripts\python -m pip install -q -r requirements-dev.txt
.\.venv\Scripts\python -m PyInstaller --noconfirm --onefile --windowed --name AutoClicker main.py

Write-Host "Готово: dist\AutoClicker.exe"
