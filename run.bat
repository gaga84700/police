@echo off
cd /d "%~dp0"
call venv\Scripts\activate
start /b python ui_main.py
