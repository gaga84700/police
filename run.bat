@echo off
cd /d "%~dp0"
set PY=f:\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\python_embeded\python.exe
start /b "" "%PY%" ui_main.py
