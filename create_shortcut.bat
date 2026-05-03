@echo off
TITLE Core Nexus — Create Desktop Shortcut

echo.
echo  Finding Python 3.12 installation...

set "PY312=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if not exist "%PY312%" set "PY312=C:\Python312\pythonw.exe"
if not exist "%PY312%" set "PY312=C:\Program Files\Python312\pythonw.exe"
if not exist "%PY312%" (
    for /f "tokens=*" %%i in ('python -c "import sys,os; print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))" 2^>nul') do set "PY312=%%i"
)

if not exist "%PY312%" (
    echo  [ERROR] Could not find Python 3.12 pythonw.exe
    echo  Checked: %LOCALAPPDATA%\Programs\Python\Python312\
    pause
    exit /b 1
)

echo  [OK] Found: %PY312%

set "PROJECT_DIR=%~dp0"
set "LAUNCHER=%PROJECT_DIR%launcher.pyw"
set "SHORTCUT=%USERPROFILE%\Desktop\Core Nexus.lnk"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%PY312%'; $s.Arguments = '\"%LAUNCHER%\"'; $s.WorkingDirectory = '%PROJECT_DIR%'; $s.Description = 'Launch Core Nexus AI'; $s.Save()"

if exist "%SHORTCUT%" (
    echo  [OK] Shortcut created: "Core Nexus" on your Desktop
    echo  Double-click it anytime to start.
) else (
    echo  [WARN] Shortcut creation failed - double-click launcher.pyw directly.
)
echo.
pause
