@echo off
echo Starting Strike Rate Capture...

REM Create venv if not exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install dependencies
echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt

REM Run the script
echo Running Strike Rate OCR...
python main.py

pause
