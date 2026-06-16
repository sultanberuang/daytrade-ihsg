@echo off
set /p USERNAME="Masukkan username GitHub Anda: "
powershell -ExecutionPolicy Bypass -File "%~dp0setup-github.ps1" -Username %USERNAME%
pause
