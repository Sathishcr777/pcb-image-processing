@echo off
title PCB AI Inspection & Photometric 3D Studio
echo ===============================================================
echo   STARTING PCB AI INSPECTION & PHOTOMETRIC 3D STUDIO (PORT 8000)
echo ===============================================================
echo.
echo Installing/Verifying Dependencies...
pip install -r requirements.txt
echo.
echo Launching Web Server at http://localhost:8000 ...
start http://localhost:8000/photometric-studio
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
pause
