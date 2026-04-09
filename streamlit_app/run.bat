@echo off
REM RajeshGPT - Streamlit Quick Start (Windows)

echo.
echo ====================================
echo    RajeshGPT - Streamlit Edition
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
pip list | findstr streamlit >nul 2>&1
if errorlevel 1 (
    echo [2/3] Installing requirements...
    pip install -r requirements.txt
) else (
    echo [2/3] Dependencies already installed
)

echo.
echo [3/3] Starting RajeshGPT...
echo.
echo ✓ Opening http://localhost:8501
echo ✓ Press CTRL+C to stop
echo.

streamlit run app.py

pause
