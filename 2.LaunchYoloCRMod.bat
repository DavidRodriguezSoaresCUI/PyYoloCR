@REM choose Python interpreter
Set "PythonInterpreter=python"
IF EXIST Python.txt (
  Set /P PythonInterpreter=<Python.txt
  @REM Because the Windows command line doesn't immediately affect 'PythonInterpreter' and we need quotes, it is done in another code block below 
)
IF EXIST Python.txt (
  Set PythonInterpreter="%PythonInterpreter%"
)
%PythonInterpreter% ./YoloCRMod.py
echo Done ! Check there was no error.
pause
