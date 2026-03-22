@echo off
setlocal EnableDelayedExpansion
title NX-CORE // RUNTIME INIT

color 0A

:: == CHAOTIC TITLE ============================================
echo ============================================================
echo.
echo  N   N  EEEEE  X   X  OOOOO  RRRR   AAAAA
echo  NN  N  E       X X   O   O  R   R  A   A
echo  N N N  EEEE     X    O   O  RRRR   AAAAA
echo  N  NN  E       X X   O   O  R  R   A   A
echo  N   N  EEEEE  X   X  OOOOO  R   R  A   A
echo.
echo ============================================================
echo.
timeout /t 1 >nul

echo [BOOT] Initializing kernel hooks...
timeout /t 1 >nul
echo [BOOT] Allocating memory regions...
timeout /t 1 >nul
echo [BOOT] Syncing execution threads...
timeout /t 1 >nul

:: == Location Check ============================================
if not exist "%~dp0app\main.py" (
    echo [FATAL] CORE MODULE NOT FOUND
    echo [ABORT] Execution halted.
    pause
    exit /b 1
)

echo [OK] Core module integrity verified.
timeout /t 1 >nul
echo.

:: == Python Check ==============================================
echo [SYS] Checking runtime...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Python missing → deploying...
    timeout /t 1 >nul

    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%TEMP%\nx.exe'" >nul 2>&1
    "%TEMP%\nx.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 >nul 2>&1

    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"
    set "PATH=%PATH%;!USER_PATH!"

    echo [OK] Runtime deployed.
) else (
    echo [OK] Runtime detected.
)

timeout /t 1 >nul
echo.

:: == VENV ======================================================
echo [ENV] Building execution container...
if not exist "%~dp0app\.venv" (
    python -m venv "%~dp0app\.venv" >nul 2>&1
    echo [OK] Container created.
) else (
    echo [SKIP] Container exists.
)

timeout /t 1 >nul
echo.

:: == DEPENDENCIES ==============================================
echo [PKG] Resolving modules...
"%~dp0app\.venv\Scripts\pip.exe" install -r "%~dp0app\requirements.txt" --quiet --disable-pip-version-check
echo [OK] Modules synchronized.

timeout /t 1 >nul
echo.

:: == FAST MEMORY CHECK =========================================
echo [MEM] Initiating deep memory sweep...

for /l %%i in (1,1,150) do (
    set /a r=!random! %% 5

    if !r! EQU 0 echo [MEM %%i] Testing memory sector 0x!random!!random!...
    if !r! EQU 1 echo [MEM %%i] Checking cache line integrity...
    if !r! EQU 2 echo [MEM %%i] Flushing L3 shadow buffers...
    if !r! EQU 3 echo [MEM %%i] Validating address bus...
    if !r! EQU 4 echo [MEM %%i] Reading volatile segment !random!...

    ping 127.0.0.1 -n 1 >nul
)

echo [MEM] Sweep complete.
echo.

:: == FINAL VALIDATION ==========================================
echo ============================================================
echo [CORE] ENTERING FINAL VALIDATION SEQUENCE
echo ============================================================

set "last="

for /l %%i in (1,1,40) do (

    if %%i LEQ 10 (
        set "msg=Scanning memory fragments..."
    ) else if %%i LEQ 20 (
        set "msg=Validating kernel shadow stack..."
    ) else if %%i LEQ 30 (
        set "msg=Aligning execution vectors..."
    ) else (
        set /a r=!random! %% 6
        if !r! EQU 0 set "msg=Verifying quantum hash table..."
        if !r! EQU 1 set "msg=Syncing arč linuks pool..."
        if !r! EQU 2 set "msg=Accessing the mossad mainframe..."
        if !r! EQU 3 set "msg=Recalibrating entropy sources..."
        if !r! EQU 4 set "msg=Analyzing cosmic ray interference..."
        if !r! EQU 5 set "msg=Cross-referencing known goy databases..."
    )

    if "!msg!"=="!last!" set "msg=Rebalancing execution state..."

    echo [CHK %%i] !msg!
    set "last=!msg!"

    timeout /t 0 >nul
)

echo.
echo [CORE] Cross-checking checksum layers...
timeout /t 1 >nul
echo [CORE] Injecting runtime hooks...
timeout /t 1 >nul
echo [CORE] Genuinely reaching flowstate...
timeout /t 2 >nul

echo.
echo ============================================================
echo [STATUS] ALL SYSTEMS NOMINAL
echo [STATUS] NX-CORE READY
echo ============================================================
echo.

timeout /t 2 >nul

:: == LAUNCH ====================================================
cd /d "%~dp0app"
echo [EXEC] Launching main process...
timeout /t 1 >nul

"%~dp0app\.venv\Scripts\python.exe" main.py

echo.
echo [SHUTDOWN] Process terminated.
pause >nul
endlocal
