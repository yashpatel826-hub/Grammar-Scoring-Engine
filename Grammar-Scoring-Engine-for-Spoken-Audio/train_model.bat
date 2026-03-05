@echo off
echo Starting model training...
echo.

cd /d "%~dp0"
call venv\Scripts\activate

python backend\train.py --epochs 20 --batch-size 8

echo.
echo Training complete! Check models\ folder for saved weights.
pause
