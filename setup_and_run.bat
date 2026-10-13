@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Chưa tìm thấy Python. Vui lòng cài Python 3.10 đến 3.12 và chọn Add Python to PATH.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Đang tạo môi trường Python...
  py -3 -m venv .venv
)

echo Đang cài đặt thư viện cần thiết...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Cài đặt thất bại. Vui lòng kiểm tra kết nối mạng và phiên bản Python.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" app.py
if errorlevel 1 pause

