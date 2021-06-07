@echo off

@REM Ask user for language to download
:ask_user
Set /P lang=Please enter Tesseract-OCR language to install (3 loweracase character code) || Set lang=NothingChosen
If "%lang%"=="NothingChosen" goto NOLANG_error
mkdir tessdata
curl https://raw.githubusercontent.com/tesseract-ocr/tessdata/master/%lang%.traineddata >tessdata/%lang%.traineddata
echo Please check the resulting file weighs at least a few MB. Otherwise, it is likely the download failed or the language code is incorrect.
pause
EXIT /B

:NOLANG_error
echo Nothing was chosen. Retrying ..
goto ask_user
