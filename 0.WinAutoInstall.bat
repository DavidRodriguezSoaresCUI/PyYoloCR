@REM Script to install some requirements for PyYoloCR. Tested on Windows 10.
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
echo %PATH% >PATH.log
python 0.WinAutoInstall.py
del PATH.log
@REM Unfortunately, passing %PATH% as argument didn't always worked, so as alternative it is written to a temporary file. 


@REM Updating pip (not mandatory, just a nice to have)
echo:
echo [2/3] Updating pip ..
python -m pip install --upgrade pip


@REM Installing Python libraries from requirements file
echo:
echo [3/3] Installing python libraries ..
python -m pip install -r requirements


@REM END OF SCRIPT
echo End of Program
pause
exit /b


@REM The following code was provided by Stack Overflow user mythofechelon at https://stackoverflow.com/a/11995662 (https://stackoverflow.com/questions/4051883/batch-script-how-to-check-for-admin-rights)
@REM Modifications : Added display of script name, 2s timeout and exit on failure
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


