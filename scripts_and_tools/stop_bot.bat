@echo off
chcp 65001 >nul
title Dừng Bot Telegram

echo ============================================
echo    DUNG BOT TELEGRAM
echo ============================================
echo.

:: Tắt tất cả Python process đang chạy
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM python3.exe /T >nul 2>&1

:: Đợi 2 giây để đảm bảo đã tắt hết
timeout /t 2 /nobreak >nul

:: Kiểm tra còn process không
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if %ERRORLEVEL% == 0 (
    echo [!] Mot so process chua tat, dang thu lai...
    taskkill /F /IM python.exe /T >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo.
echo [OK] Bot da duoc tat hoan toan!
echo.
echo Bam phim bat ky de dong cua so nay...
pause >nul
