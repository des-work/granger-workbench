@echo off
setlocal enabledelayedexpansion
title Ultra-PC

rem NOTE: we do NOT cd into the script folder. ultra.py anchors all its own
rem paths to __file__ (see core.ROOT), so staying in the caller's directory
rem lets relative file arguments work, e.g.  ultra md notes.md

rem --- Find a Python that has the required packages (prefer 3.11) -----------
set "PYEXE="

rem 1) py launcher, version 3.11 (where psutil/Pillow/numpy live)
py -3.11 -c "import sys" >nul 2>&1 && set "PYEXE=py -3.11"

rem 2) known 3.11 install path
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
  set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

rem 3) whatever 'python' resolves to
if not defined PYEXE (
  where python >nul 2>&1 && set "PYEXE=python"
)

rem 4) last resort: default py launcher
if not defined PYEXE (
  where py >nul 2>&1 && set "PYEXE=py"
)

if not defined PYEXE (
  echo.
  echo Could not find Python. Install Python 3.11+ from https://python.org
  echo and re-run this file.
  pause
  exit /b 1
)

rem Pass through any arguments, e.g.  ultra.bat kb "how NTFS works"
%PYEXE% "%~dp0ultra.py" %*
set "RC=%ERRORLEVEL%"

rem Pause only when double-clicked with no args (so the window stays open)
if "%~1"=="" if not "%RC%"=="0" pause
exit /b %RC%
