@echo off
REM Windows setup script for Water Quality Data Pipeline

echo =========================================
echo Water Quality Data Pipeline Setup
echo =========================================
echo.

REM Check Python version
echo Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist .venv (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv .venv
    echo Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo All dependencies installed successfully
echo.

REM Run data cleaning
echo Processing data...
python data_cleaning.py
if errorlevel 1 (
    echo ERROR: Data cleaning failed
    pause
    exit /b 1
)
echo Data cleaned successfully
echo.

REM Setup database
echo Setting up database...
python database_setup.py
if errorlevel 1 (
    echo ERROR: Database setup failed
    pause
    exit /b 1
)
echo Database setup complete
echo.

echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo To start the application:
echo.
echo 1. Activate virtual environment:
echo    .venv\Scripts\activate
echo.
echo 2. Start the API server:
echo    python api/flaskAPI.py
echo.
echo 3. In a new terminal, start the dashboard:
echo    streamlit run client/streamlit_client.py
echo.
echo 4. Open your browser to:
echo    http://localhost:8501
echo.
pause
