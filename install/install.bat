@echo off
@setlocal enableextensions
@cd /d "%~dp0"
cls
python -m pip install dropbox
python -m pip install psutil
python -m pip install requests
copy /y "%~dp0\ffmpeg.exe" "C:\windows\ffmpeg.exe"
pause
