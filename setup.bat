@echo off
setlocal
title LLM Council Setup

echo ===================================================
echo           LLM Council - Installation Setup
echo ===================================================
echo.

:: 1. Check Prerequisites
echo [1/4] Checking System Requirements...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org
    pause
    exit /b
)
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from nodejs.org
    pause
    exit /b
)
echo Python and Node.js detected.
echo.

:: 2. Backend Setup
echo [2/4] Setting up Backend...
cd server
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate

echo Installing Backend Dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b
)
cd ..
echo.

:: 3. Frontend Setup
echo [3/4] Setting up Frontend...
cd client
echo Installing Frontend Dependencies (this may take a moment)...
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node modules.
    pause
    exit /b
)
cd ..
echo.

:: 4. Configuration Check
echo [4/4] Verifying Configuration...
if not exist server\.env (
    echo.
    echo [ATTENTION] 'server\.env' file is missing!
    echo Creating a template for you...
    echo GEMINI_API_KEY=Replace_With_Your_Key > server\.env
    echo GEMINI_MODEL=gemini-2.0-flash-exp >> server\.env
    echo.
    echo ******************************************************
    echo *  IMPORTANT: Open 'server\.env' and paste your API Key  *
    echo ******************************************************
) else (
    echo Configuration found.
)

echo.
echo ===================================================
echo           SETUP COMPLETE! 🚀
echo ===================================================
echo.
echo You can now run the app using 'run_dev.bat'
echo.
pause
