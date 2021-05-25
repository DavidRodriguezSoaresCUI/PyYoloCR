@REM Script to install requirements for Windows 10
@echo off


@REM Require admin
call :check_Permissions
@REM Get back to launch directory
@setlocal enableextensions
@cd /d "%~dp0"
echo:
echo This script tries to install VapourSynth plugins and python libraries needed for PyYoloCR.
@REM Launch script
echo:
echo [1/3] Installing VapourSynth plugins ..
python 0.WinAutoInstall.py "%PATH%"
echo:
echo [2/3] Updating pip ..
python -m pip install --upgrade pip
echo:
echo [3/3] Installing python libraries ..
python -m pip install -r requirements
@REM End
echo End of Program
pause
exit /b


:check_Permissions
    echo Administrative permissions required. Detecting permissions...
	Set scriptname="%~n0%~x0"
    net session >nul 2>&1
    if %errorLevel% == 0 (
        echo Running %scriptname% with Administrative permissions
    ) else (
        echo Failure: Current permissions inadequate. Please run %scriptname% with Administrative permissions.
        pause
        EXIT
    )
	echo:
    timeout /t 2 1>nul
EXIT /B


