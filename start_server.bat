@echo off
cd /d "%~dp0"
title Do It App Server

:: Add firewall rule for HTTPS port
net session >nul 2>&1
if %errorlevel% == 0 (
    netsh advfirewall firewall delete rule name="Do It App" >nul 2>&1
    netsh advfirewall firewall add rule name="Do It App" dir=in action=allow protocol=TCP localport=8443 profile=any >nul
    echo   [OK] Firewall rule set for port 8443
) else (
    echo   [!] Not running as admin - right-click and Run as administrator if phone cannot connect.
    echo.
)

:: Install cryptography package if needed
py -c "import cryptography" >nul 2>&1
if errorlevel 1 (
    echo   Installing required package...
    py -m pip install cryptography --quiet
)

echo.
echo ====================================================
echo   Do It - Daily To-Do  (HTTPS)
echo ====================================================
echo.

:: Start HTTPS server (use py launcher which resolves correctly on this machine)
py --version >nul 2>&1
if not errorlevel 1 (
    py server.py
    echo.
    echo   Server stopped. Press any key to close.
    pause >nul
    goto :eof
)

echo   ERROR: Python not found.
echo   Install Python from python.org, then try again.
echo.
pause
