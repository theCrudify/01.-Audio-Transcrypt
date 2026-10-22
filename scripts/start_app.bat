@echo off
cd /d "%~dp0\.."
set "KMP_DUPLICATE_LIB_OK=TRUE"

where python >nul 2>&1
if errorlevel 1 (
    echo Python tidak ditemukan di PATH.
    echo Buka Anaconda Prompt atau aktifkan virtual environment terlebih dahulu.
    pause
    exit /b 1
)

echo.
echo Checking environment...
python -m app.verify
if errorlevel 1 (
    echo.
    echo Setup failed. Install dependencies first:
    echo     python -m pip install -r requirements\base.txt
    pause
    exit /b 1
)

echo.
echo Starting Local AI Transcription Studio...
python -m app.main
