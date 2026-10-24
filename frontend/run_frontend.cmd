@echo off
setlocal

cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found on PATH. Install Node.js, then run this file again.
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo npm was not found on PATH. Install Node.js with npm, then run this file again.
  exit /b 1
)

set NEED_INSTALL=0
if not exist "node_modules\next\package.json" set NEED_INSTALL=1
if not exist "node_modules\@tailwindcss\postcss\package.json" set NEED_INSTALL=1

if "%NEED_INSTALL%"=="1" (
  echo Installing frontend packages...
  call npm.cmd ci
  if errorlevel 1 goto :install_failed
  if not exist "node_modules\next\package.json" goto :install_failed
  if not exist "node_modules\@tailwindcss\postcss\package.json" goto :install_failed
)

echo Starting Apron website at http://127.0.0.1:3000
call npm.cmd run dev
exit /b %errorlevel%

:install_failed
echo Frontend package install failed. Close any other frontend server, then run npm.cmd ci in this folder.
exit /b 1
