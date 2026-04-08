@echo off
title LLM Council Launcher
echo ===================================================
echo           Starting LLM Council...
echo ===================================================

if not exist server\venv (
    echo [ERROR] Virtual environment not found.
    echo Please run 'setup.bat' first.
    pause
    exit /b
)

echo.
echo 1. Launching Backend (Port 8000)...
start "LLM Council Backend" cmd /k "cd server && venv\Scripts\activate && uvicorn main:app --reload"

echo 2. Launching Frontend (Port 5173)...
start "LLM Council Frontend" cmd /k "cd client && npm run dev"

echo.
echo ===================================================
echo           App is Running! 🚀
echo ===================================================
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000/docs (Swagger UI)
echo.
echo Keep this window open or minimize it. 
echo Closing the other windows will stop the servers.
pause
