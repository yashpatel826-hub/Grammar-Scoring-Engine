@echo off
echo Starting Grammar Scoring Engine API Server...
echo.

cd /d "%~dp0"
call venv\Scripts\activate

echo Server running at http://localhost:8000
echo API Docs at http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.

python backend\api.py
