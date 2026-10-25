@echo off
rem Lance la demo : verifie Ollama, demarre le serveur et ouvre la page dans le navigateur.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Environnement Python absent : lance d'abord installer.bat
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\demarrer.py %*
if errorlevel 1 pause
