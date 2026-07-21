@echo off
REM ===================================================================
REM  Latoun Configurator - start backend + frontend (Windows)
REM ===================================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv not found. Run setup_local.bat first.
    exit /b 1
)

echo Starting FastAPI backend on http://localhost:8000 ...
start "Latoun Backend" cmd /k "call "%~dp0.venv\Scripts\activate.bat" && cd /d "%~dp0backend" && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Vite frontend on http://localhost:5173 ...
start "Latoun Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

REM Give the dev servers a moment to boot before opening the browser.
timeout /t 5 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo Backend and frontend are launching in separate windows.
echo Close those windows (or press Ctrl+C in each) to stop the app.
echo.
