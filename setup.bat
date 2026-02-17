@echo off
:: YouTube Downloader Setup Launcher
:: This batch file runs the PowerShell setup script

title YouTube Downloader - Setup

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This setup can run without admin rights.
    echo Files will be installed locally.
    echo.
    timeout /t 3 >nul
)

:: Run the PowerShell setup script
powershell -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

pause