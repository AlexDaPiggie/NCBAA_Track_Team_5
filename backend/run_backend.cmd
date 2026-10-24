@echo off
setlocal

cd /d "%~dp0\.."

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on PATH.
  echo Activate your Python environment or add Python to PATH, then run this file again.
  exit /b 1
)

python -c "import fastapi, uvicorn, simpy, numpy, pandas" >nul 2>nul
if errorlevel 1 (
  echo Backend packages are missing from the active Python environment.
  echo Install them with: python -m pip install -r backend\requirements.txt
  exit /b 1
)

if not exist "backend\data\trained_forecast.json" (
  echo Creating the synthetic forecast model...
  python -m backend.training
  if errorlevel 1 exit /b 1
)

echo Starting Apron API at http://127.0.0.1:8000
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
