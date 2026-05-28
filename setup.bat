@echo off
REM XARA Backend Setup Script for Windows

echo ================================
echo XARA Smart Signage - Backend Setup
echo ================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Python is installed

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ^✓ Virtual environment created
) else (
    echo ^✓ Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt >nul 2>&1
echo ^✓ Dependencies installed

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo ^✓ .env file created from template
    echo.
    echo WARNING: Please update .env with your MongoDB connection string and secrets
) else (
    echo ^✓ .env file already exists
)

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo To start the server, run:
echo   python run.py
echo.
echo API Documentation:
echo   http://localhost:8000/docs
echo.

pause
