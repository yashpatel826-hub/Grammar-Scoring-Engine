@echo off
echo ========================================
echo Grammar Scoring Engine - End-to-End Start
echo ========================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate" (
	call .venv\Scripts\activate
) else (
	if exist "venv\Scripts\activate" (
		call venv\Scripts\activate
	) else (
		echo [ERROR] No virtual environment found. Run setup.bat first.
		pause
		exit /b 1
	)
)

echo [1/2] Building frontend...
cd frontend
call npm run build
if errorlevel 1 (
	echo [ERROR] Frontend build failed.
	pause
	exit /b 1
)

echo.
echo [2/2] Starting backend API (serves frontend dist)...
cd ..
echo.
echo App:      http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.

python backend\api.py
