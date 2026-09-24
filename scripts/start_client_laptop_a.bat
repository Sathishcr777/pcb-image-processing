@echo off
echo ===================================================
echo   STARTING PCB AI CAMERA CLIENT (LAPTOP A)
echo ===================================================
echo.

set /p LAPTOP_B_IP="Enter Laptop B IP Address (e.g. 192.168.1.100): "

if "%LAPTOP_B_IP%"=="" set LAPTOP_B_IP=192.168.1.100

echo.
echo Connecting to http://%LAPTOP_B_IP%:8000/inspect ...
echo.

cd /d "%~dp0\.."
python client/capture_and_send.py http://%LAPTOP_B_IP%:8000/inspect

pause
