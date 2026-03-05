@echo off
echo ========================================
echo Grammar Scoring Engine - Setup Script
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate

echo.
echo [2/4] Installing backend dependencies...
pip install -r backend\requirements.txt

echo.
echo [3/4] Creating required directories...
if not exist "models" mkdir models
if not exist "transcripts" mkdir transcripts
if not exist "uploads" mkdir uploads

echo.
echo [4/4] Setup complete!
echo.
echo ========================================
echo To start the application:
echo   1. Activate venv: venv\Scripts\activate
echo   2. Train model:   python backend\train.py
echo   3. Start API:     python backend\api.py
echo   4. Open frontend: frontend\index.html
echo ========================================
pause
