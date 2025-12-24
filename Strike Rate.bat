@echo off
echo Starting Strike Rate Capture...

REM Use venv Python
set PYTHON_PATH=D:\UST PROJECT\venv34\Scripts\python.exe

REM Go to project folder
cd /d D:\UST PROJECT

REM Run script
"%PYTHON_PATH%" main.py

pause
