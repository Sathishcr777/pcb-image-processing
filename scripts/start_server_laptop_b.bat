@echo off
echo ===================================================
echo   STARTING PCB AI INSPECTION SERVER (LAPTOP B)
echo ===================================================
echo.

cd /d "%~dp0\.."

echo 1. Checking dependencies...
pip install fastapi uvicorn[standard] python-multipart opencv-python numpy scipy pandas pillow scikit-image >nul 2>&1

echo 2. Launching FastAPI Server on 0.0.0.0:8000...
echo Server IP will be accessible on Laptop A!
echo.

python -m uvicorn server.main:app --host 0.0.0.0 --port 8000

pause
