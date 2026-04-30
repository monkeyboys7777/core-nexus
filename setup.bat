@echo off
TITLE Core Nexus — Setup
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       CORE NEXUS — Setup Utility             ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)
echo  [OK] Python found.

:: Check pip
pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] pip not found.
    pause
    exit /b 1
)
echo  [OK] pip found.

:: Install requirements
echo.
echo  Installing dependencies...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo  [WARN] Some packages failed. Check output above.
    echo         pyaudio sometimes needs manual install on Windows:
    echo         pip install pipwin ^& pipwin install pyaudio
) ELSE (
    echo  [OK] Dependencies installed.
)

:: Check for ANTHROPIC_API_KEY
echo.
IF "%ANTHROPIC_API_KEY%"=="" (
    echo  [WARN] ANTHROPIC_API_KEY is not set as an environment variable.
    echo.
    echo  To set it permanently, run this in PowerShell as Admin:
    echo    [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","your-key-here","User")
    echo.
    echo  Or set it temporarily for this session:
    set /p NEXUS_KEY="  Paste your API key now (or press Enter to skip): "
    IF NOT "%NEXUS_KEY%"=="" (
        set ANTHROPIC_API_KEY=%NEXUS_KEY%
        echo  [OK] Key set for this session only.
    )
) ELSE (
    echo  [OK] ANTHROPIC_API_KEY is set.
)

echo.
echo  ────────────────────────────────────────────────
echo  NEXT STEPS:
echo    1. Edit config.json with your actual app paths
echo    2. Run:  python core_nexus.py          (voice mode)
echo         or: python core_nexus.py --text   (text mode / testing)
echo  ────────────────────────────────────────────────
echo.
pause
