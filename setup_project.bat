@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo        Sting Operation AI - Local Setup
echo ===================================================

cd /d "%~dp0"

:: 1. Create virtual environment
echo.
echo [1/4] Setting up Python virtual environment...
if not exist ".venv" (
    echo Virtual environment not found. Creating .venv...
    :: Try using uv if available, otherwise fallback to python -m venv
    where uv >nul 2>nul
    if !errorlevel! equ 0 (
        uv venv
    ) else (
        python -m venv .venv
    )
) else (
    echo .venv virtual environment already exists.
)

:: 2. Install dependencies
echo.
echo [2/4] Installing dependencies...
where uv >nul 2>nul
if !errorlevel! equ 0 (
    echo Using uv to install shared core and dependencies...
    uv pip install git+https://github.com/fivepanelhat/coastal-alpine-core.git
    uv pip install -r requirements.txt
    uv pip install -r requirements-dev.txt
) else (
    echo Using pip to install shared core and dependencies...
    .venv\Scripts\pip install git+https://github.com/fivepanelhat/coastal-alpine-core.git
    .venv\Scripts\pip install -r requirements.txt
    .venv\Scripts\pip install -r requirements-dev.txt
)

:: 3. Run tidy-up and class-fix scripts
echo.
echo [3/4] Running repository cleanup and class-mapping corrections...
.venv\Scripts\python tools\tidy_and_fix.py

:: 4. Run verification
echo.
echo [4/4] Verifying setup integrity...
.venv\Scripts\python tools\verify_setup.py

echo.
echo ===================================================
echo Setup Process Finished!
echo To run inference:
echo   .venv\Scripts\python predict.py data/images/val/985d1c64-8272-47e7-9fd2-1b7a2399a189_jpg.rf.6e92e8483f9bd8f94270a7256149f481.jpg
echo ===================================================
pause
