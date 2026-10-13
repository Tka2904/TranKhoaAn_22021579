@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Vui lòng chạy setup_and_run.bat trước.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" tools\calibrate_camera.py --images calibration_images --cols 6 --rows 6 --square-mm 25 --output calibration.npz
pause

