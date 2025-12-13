@echo off
cd /d "%~dp0"

REM Try ComfyUI Python first (has latest CUDA support)
set COMFY_PY=f:\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\python_embeded\python.exe
if exist "%COMFY_PY%" (
    echo Using ComfyUI Python for GPU support...
    "%COMFY_PY%" ui_main.py
    exit /b
)

REM Fallback to local venv
if exist "venv\Scripts\python.exe" (
    echo Using local venv...
    call venv\Scripts\activate.bat
    python ui_main.py
    exit /b
)

REM Last resort: system Python
echo Using system Python...
python ui_main.py
