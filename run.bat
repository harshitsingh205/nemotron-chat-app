@echo off
setlocal
echo ==============================================
echo   Nemotron Reasoning Chat - Streamlit Launcher
echo ==============================================

rem Check if local python_embed exists
if exist "%~dp0..\python_embed\python.exe" (
    set "PYTHON_EXE=%~dp0..\python_embed\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Using Python: %PYTHON_EXE%
echo Installing / checking requirements...
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt"

echo Launching Streamlit web app...
"%PYTHON_EXE%" -m streamlit run "%~dp0app.py"
pause
