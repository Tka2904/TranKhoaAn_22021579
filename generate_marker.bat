@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Vui lòng chạy setup_and_run.bat trước.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" tools\generate_marker.py --size-mm 50 --id 0
pause

