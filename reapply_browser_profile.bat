@echo off
REM ============================================================
REM  Reapply Browser Profile
REM  Copies the backed-up warmed browser profile back to the
REM  system location that AutoBrowser / MCP browser tool uses.
REM ============================================================

set SRC=%~dp0_browser_profile_backup
set DST=%LOCALAPPDATA%\.nakedweb\browser_profile

echo.
echo  ===== Reapply Browser Profile =====
echo.
echo  Source:  %SRC%
echo  Target:  %DST%
echo.

if not exist "%SRC%" (
    echo  ERROR: Backup folder not found at %SRC%
    echo  Run the warmup tool first to create a profile.
    pause
    exit /b 1
)

echo  Copying profile data...
xcopy "%SRC%" "%DST%" /E /I /H /Y /Q >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo  Done! Profile restored successfully.
) else (
    echo  ERROR: Copy failed with code %ERRORLEVEL%
)

echo.
pause
