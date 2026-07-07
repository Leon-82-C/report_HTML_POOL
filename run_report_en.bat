@echo off
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "DATA_DIR=%CD%"

if exist "GK*" (
    for /f "delims=" %%d in ('dir /b /ad "GK*" 2^>nul') do (
        set "DATA_DIR=%CD%\%%d"
        goto :found_data
    )
)

:found_data

REM Locate report_generator_en.py
set "PYTHON_SCRIPT="
if exist "%SCRIPT_DIR%report_generator_en.py" (
    set "PYTHON_SCRIPT=%SCRIPT_DIR%report_generator_en.py"
    goto :found_script
)
if exist "%SCRIPT_DIR%..\report_generator_en.py" (
    set "PYTHON_SCRIPT=%SCRIPT_DIR%..\report_generator_en.py"
    goto :found_script
)
if exist "E:\work\report_HTML_POOL\report_generator_en.py" (
    set "PYTHON_SCRIPT=E:\work\report_HTML_POOL\report_generator_en.py"
    goto :found_script
)

:found_script
if "%PYTHON_SCRIPT%"=="" (
    echo ERROR: report_generator_en.py not found!
    pause
    exit /b 1
)

echo Enter sample name:
set /p SAMPLE_INPUT=
if "%SAMPLE_INPUT%"=="" (
    set SAMPLE_ARG=
) else (
    set SAMPLE_ARG=--sample "%SAMPLE_INPUT%"
)

echo Enter protocol number:
set /p PROTOCOL_INPUT=
if "%PROTOCOL_INPUT%"=="" (
    set PROTOCOL_ARG=
) else (
    set PROTOCOL_ARG=--protocol "%PROTOCOL_INPUT%"
)

python "%PYTHON_SCRIPT%" "%DATA_DIR%" "report_output_en" %SAMPLE_ARG% %PROTOCOL_ARG%

echo.
pause
