@echo off
cd /d "%~dp0\.."
set "KMP_DUPLICATE_LIB_OK=TRUE"

rem Any Python 3.10+ works for setup (python.org, Anaconda, or the py launcher); it creates .venv on the first run.
set "PY="
set "PYARGS="
set "USERPY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
rem "python" may be the Microsoft Store stub, so check that it really runs.
if not defined PY python -c "import sys" >nul 2>&1 && set "PY=python"
if not defined PY py -3 -c "import sys" >nul 2>&1 && set "PY=py" && set "PYARGS=-3"
if not defined PY if exist "%USERPY%" set "PY=%USERPY%"
if not defined PY (
    rem First run without Python: install the official python.org build via winget (per-user, no admin needed).
    where winget >nul 2>&1 && (
        echo Python belum terpasang. Menginstall Python 3.12 lewat winget ...
        winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
    )
    if exist "%USERPY%" set "PY=%USERPY%"
)
if not defined PY (
    echo Python tidak ditemukan dan tidak bisa diinstall otomatis.
    echo Install Python 3.10+ dari https://www.python.org/downloads/ ^(centang "Add python.exe to PATH"^), lalu jalankan ulang.
    pause
    exit /b 1
)

echo.
echo Preparing files (first run downloads ~650 MB)...
"%PY%" %PYARGS% -m app.bootstrap
if errorlevel 1 (
    echo.
    echo Setup gagal. Baca pesan [setup] di atas, perbaiki, lalu jalankan ulang script ini.
    pause
    exit /b 1
)
set "PY=.venv\Scripts\python.exe"

echo.
echo Checking environment...
"%PY%" -m app.verify
if errorlevel 1 (
    echo.
    echo Pengecekan gagal. Lihat pesan di atas.
    pause
    exit /b 1
)

echo.
echo Starting Local AI Transcription Studio...
"%PY%" -m app.main
