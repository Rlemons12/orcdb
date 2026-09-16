@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=py"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python was not found.
            echo Create the virtual environment and install requirements first.
            pause
            exit /b 1
        )
        set "PYTHON=python"
    )
)

echo Starting Oracle DB Reporting System...
echo Open http://127.0.0.1:5010 in your browser.
echo.
%PYTHON% run_app.py

if errorlevel 1 (
    echo.
    echo The application stopped with an error.
    pause
)
