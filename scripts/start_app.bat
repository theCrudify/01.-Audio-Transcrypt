@echo off
cd /d "%~dp0\.."
set "KMP_DUPLICATE_LIB_OK=TRUE"

rem Any Python 3.10+ works for setup (python.org, Anaconda, or the py launcher); it creates .venv on the first run.
set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    echo Python tidak ditemukan.
    echo Install Python 3.10+ dari https://www.python.org/downloads/ ^(centang "Add python.exe to PATH"^).
    pause
    exit /b 1
)

echo.
echo Preparing files (first run downloads ~600 MB)...
%PY% -m app.bootstrap
if errorlevel 1 (
    echo.
    echo Setup gagal. Baca pesan [setup] di atas, perbaiki, lalu jalankan ulang script ini.
    pause
    exit /b 1
)
set "PY=.venv\Scripts\python.exe"

echo.
echo Checking environment...
%PY% -m app.verify
if errorlevel 1 (
    echo.
    echo Pengecekan gagal. Lihat pesan di atas.
    pause
    exit /b 1
)

echo.
echo Starting Local AI Transcription Studio...
%PY% -m app.main
