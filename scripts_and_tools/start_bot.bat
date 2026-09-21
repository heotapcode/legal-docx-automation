@echo off
chcp 65001 >nul
title Bot Telegram - Ho So Tu Dong

echo ============================================
echo    BOT TELEGRAM - HO SO TU DONG
echo ============================================
echo.

:: Bước 1: Tắt toàn bộ Python đang chạy
echo [1/3] Dang tat cac phien bot cu...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM python3.exe /T >nul 2>&1
timeout /t 3 /nobreak >nul
echo      Done!

:: Bước 2: Chuyển vào thư mục dự án
cd /d "%~dp0"
echo [2/3] Thu muc: %CD%

:: Bước 3: Khởi động bot
echo [3/3] Dang khoi dong bot...
echo.
echo ============================================
echo    BOT DANG CHAY - De tat: Nhan Ctrl+C
echo    Hoac double-click file stop_bot.bat
echo ============================================
echo.

set PYTHONIOENCODING=utf-8
python telegram_bot.py

echo.
echo Bot da dung. Bam phim bat ky de dong...
pause >nul
