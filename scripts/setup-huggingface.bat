@echo off
set /p HFUSER="Masukkan username Hugging Face Anda: "
powershell -ExecutionPolicy Bypass -File "%~dp0setup-huggingface.ps1" -Username %HFUSER%
pause
