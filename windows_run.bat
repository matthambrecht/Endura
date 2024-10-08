@echo off
IF NOT EXIST "venv" (
    python -m venv venv
    PowerShell -ExecutionPolicy Bypass -File venv\bin\Activate.ps1
    pip install -r requirements.txt
) ELSE (
    PowerShell -ExecutionPolicy Bypass -File venv\bin\Activate.ps1
)

python app\app.py
