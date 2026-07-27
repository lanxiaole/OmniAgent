@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=%PROJECT_ROOT%.venv"
set "PYTHON=%VENV_PATH%\Scripts\python.exe"
set "UVICORN=%VENV_PATH%\Scripts\uvicorn.exe"

echo ========================================
echo           OmniAgent Launcher
echo ========================================
echo.

if not exist "%VENV_PATH%" (
    echo Error: Virtual environment not found at %VENV_PATH%
    echo Please run: uv sync
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
"%PYTHON%" --version
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [2/3] Starting backend service...
echo       Backend: http://localhost:8000
start "OmniAgent Backend" cmd /k cd /d "%PROJECT_ROOT%" && "%UVICORN%" backend.main:app --reload --port 8000
timeout /t 3 /nobreak >nul

echo.
echo [3/3] Starting frontend dev server...
echo       Frontend: http://localhost:5173
start "OmniAgent Frontend" cmd /k cd /d "%PROJECT_ROOT%frontend" && npm run dev
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo           Services Started
echo ========================================
echo.
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8000
echo.
echo Press any key to exit...
pause >nul