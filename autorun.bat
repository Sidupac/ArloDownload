@echo off
@setlocal enableextensions
@cd /d "%~dp0"
cls

set CUR_YYYY=%date:~10,4%
set CUR_MM=%date:~4,2%
set CUR_DD=%date:~7,2%

set CUR_HH=%time:~0,2%
if %CUR_HH% lss 10 (set CUR_HH=0%time:~1,1%)

set CUR_MN=%time:~3,2%
set CUR_SS=%time:~6,2%
set CUR_MS=%time:~9,2%

if not exist "%~dp0logs\" mkdir "%~dp0logs\"

cls

echo "%~dp0ArloDownload.py"
"python.exe" "%~dp0ArloDownload.py">"%~dp0logs\%CUR_YYYY%.%CUR_MM%.%CUR_DD%-%CUR_HH%.%CUR_MN%.%CUR_SS%.txt"
