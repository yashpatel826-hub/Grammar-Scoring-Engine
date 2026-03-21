@echo off
echo ========================================
echo Grammar Scoring Engine - Setup Script
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] Creating Python virtual environment...
python -m venv .venv
call .venv\Scripts\activate

echo.
echo [2/5] Installing backend dependencies...
pip install -r backend\requirements.txt

echo.
echo [3/5] Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo [4/5] Creating required directories...
if not exist "models" mkdir models
if not exist "transcripts" mkdir transcripts
if not exist "uploads" mkdir uploads

echo.
echo [5/5] Setup complete!
echo.
echo ========================================
echo To start the application:
echo   1. Train model:        train_model.bat
echo   2. Run full project:   run_server.bat
echo      (serves UI + API at http://localhost:8000)
echo ========================================
pause
