@echo off
cd /d "%~dp0\.."
set "KMP_DUPLICATE_LIB_OK=TRUE"

rem Prefer the project venv, then any Python on PATH (python.org, Anaconda, or the py launcher).
set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    echo Python tidak ditemukan.
    echo Install Python 3.10+ dari https://www.python.org/downloads/ ^(centang "Add python.exe to PATH"^),
    echo atau pakai paket portable AudioTranscrypt-windows.zip yang tidak butuh Python.
    pause
    exit /b 1
)

echo.
echo Checking environment...
%PY% -m app.verify
if errorlevel 1 (
    echo.
    echo Setup failed. Install dependencies first:
    echo     %PY% -m pip install -r requirements\base.txt
    pause
    exit /b 1
)

echo.
echo Starting Local AI Transcription Studio...
%PY% -m app.main
