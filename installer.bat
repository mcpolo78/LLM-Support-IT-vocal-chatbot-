@echo off
rem Installe la demo : environnement Python, dependances, modeles Ollama, voix Piper et Whisper.
rem Prerequis : pilote NVIDIA, Python 3.10 ou plus, Ollama. Relancer ce script ne casse rien.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement Python .venv
  py -3 -m venv .venv || python -m venv .venv
  if not exist ".venv\Scripts\python.exe" goto erreur
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erreur
".venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-voix.txt
if errorlevel 1 goto erreur
".venv\Scripts\python.exe" scripts\installer.py
if errorlevel 1 goto erreur
echo.
echo Installation terminee. Double-clique sur demarrer.bat pour lancer la demo.
pause
exit /b 0

:erreur
echo.
echo L'installation s'est arretee : lis le message ci-dessus.
pause
exit /b 1
