@echo off
title NAC Webapp v2 - Ho So Doanh Nghiep (Port 8002)
chcp 65001 >nul

echo ===================================================
echo     KHOI DONG NAC WEBAPP V2 (JINJA2 / DOCXTPL)
echo ===================================================
echo.

cd /d "%~dp0"

:: Tim duong dan Python phu hop
set "PY_EXE=C:\Users\Pc\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

echo Dang khoi chay may chu tai http://localhost:8002 ...
echo Bam Ctrl+C de dung may chu.
echo.

:: Mo trinh duyet sau 1 giay
start "" "http://localhost:8002"

:: Chay FastAPI Uvicorn
"%PY_EXE%" -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

pause
