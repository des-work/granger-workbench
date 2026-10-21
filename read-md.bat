@echo off
rem Ultra-PC: render a markdown file to clean text and open it in Notepad.
rem Used by the .md right-click "Read clean (Ultra-PC)" menu, and handy for
rem drag-and-drop: drop a .md file onto this .bat.
rem
rem We render with --out (UTF-8 file write) rather than piping stdout, because
rem redirected Python stdout on Windows uses the ANSI codepage and would mangle
rem the Unicode math (η, ∫, subscripts).

setlocal
if "%~1"=="" (
  echo Usage: drop a .md file onto this, or right-click a .md and pick "Read clean".
  pause
  exit /b 1
)

set "TMPOUT=%TEMP%\ultra-md-%RANDOM%%RANDOM%.txt"
call "%~dp0ultra.bat" md "%~1" --out "%TMPOUT%" >nul 2>&1

if exist "%TMPOUT%" (
  start "" notepad "%TMPOUT%"
) else (
  echo Could not render "%~1".
  pause
  exit /b 1
)
