@echo off
chcp 65001 >nul
echo ============================================
echo   CRISPR Library Sequencing Report Generator
echo ============================================
echo.

set "SCRIPT_DIR=%~dp0"
set "DATA_DIR=%CD%"

if exist "GK*" (
    for /f "delims=" %%d in ('dir /b /ad "GK*" 2^>nul') do (
        set "DATA_DIR=%CD%\%%d"
        goto :found_data
    )
)

:found_data
echo Using data directory: %DATA_DIR%
echo.

REM Locate report_generator.py: SCRIPT_DIR first, then parent dir, then E:\work\report_HTML_POOL
set "PYTHON_SCRIPT="
if exist "%SCRIPT_DIR%report_generator.py" (
    set "PYTHON_SCRIPT=%SCRIPT_DIR%report_generator.py"
    goto :found_script
)
if exist "%SCRIPT_DIR%..\report_generator.py" (
    set "PYTHON_SCRIPT=%SCRIPT_DIR%..\report_generator.py"
    goto :found_script
)
if exist "E:\work\report_HTML_POOL\report_generator.py" (
    set "PYTHON_SCRIPT=E:\work\report_HTML_POOL\report_generator.py"
    goto :found_script
)

:found_script
if "%PYTHON_SCRIPT%"=="" (
    echo ERROR: report_generator.py not found!
    pause
    exit /b 1
)
echo Using script: %PYTHON_SCRIPT%
echo.

echo Enter protocol number (press Enter to skip):
set /p PROTOCOL_INPUT=
if "%PROTOCOL_INPUT%"=="" (
    set PROTOCOL_ARG=
    echo Protocol number: (not provided)
) else (
    set PROTOCOL_ARG=--protocol "%PROTOCOL_INPUT%"
    echo Protocol number: %PROTOCOL_INPUT%
)
echo.

python "%PYTHON_SCRIPT%" "%DATA_DIR%" "report_output" %PROTOCOL_ARG%

echo.
echo Press any key to exit...
pause >nul