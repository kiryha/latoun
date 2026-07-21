@echo off
REM ===================================================================
REM  Latoun Configurator - one-time local setup (Windows)
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo === Latoun Configurator setup ===
echo.

REM --- 1. Verify Python -------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3.11+ and retry.
    exit /b 1
)
for /f "delims=" %%v in ('python --version') do echo [OK] %%v

REM --- 2. Verify Node and npm ----------------------------------------
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found on PATH. Install Node.js 20 LTS+ and retry.
    exit /b 1
)
for /f "delims=" %%v in ('node --version') do echo [OK] Node %%v

call npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm was not found on PATH. Install Node.js 20 LTS+ and retry.
    exit /b 1
)
for /f "delims=" %%v in ('call npm --version') do echo [OK] npm %%v

REM --- 3. Create virtual environment if missing --------------------
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating Python virtual environment at .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo [OK] Virtual environment already exists.
)

REM --- 4. Install backend dependencies ----------------------------
echo.
echo Installing backend Python dependencies ...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies.
    exit /b 1
)

REM --- 5. Install frontend dependencies ---------------------------
echo.
echo Installing frontend dependencies (npm install) ...
pushd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] npm install failed.
    popd
    exit /b 1
)
popd

REM --- 6. Initialize and seed the database ------------------------
echo.
echo Initializing and seeding SQLite database ...
pushd backend
"..\.venv\Scripts\python.exe" -m app.seed
if errorlevel 1 (
    echo [ERROR] Database seeding failed.
    popd
    exit /b 1
)
popd

echo.
echo ===================================================================
echo  Setup complete.
echo.
echo  Next step:  run_local.bat
echo  App URL:    http://localhost:5173
echo  API docs:   http://localhost:8000/docs
echo ===================================================================
echo.
endlocal
