@echo off
cd /d "%~dp0"
if exist "dist\department-view\ApronStaffingLab\ApronStaffingLab.exe" (
    start "" "dist\department-view\ApronStaffingLab\ApronStaffingLab.exe"
) else if exist "dist\ApronStaffingLab\ApronStaffingLab.exe" (
    start "" "dist\ApronStaffingLab\ApronStaffingLab.exe"
) else (
    echo Build the program first: powershell -ExecutionPolicy Bypass -File build-desktop.ps1
    pause
)
