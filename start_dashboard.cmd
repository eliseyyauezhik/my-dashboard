@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0start_dashboard.ps1" -Open
