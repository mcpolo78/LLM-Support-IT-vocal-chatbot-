"""Fin de l'installation : modèles Ollama, voix Piper et modèle Whisper, puis vérifications.

Appelé par installer.bat, une fois les dépendances Python installées dans .venv.
"""
import subprocess
import sys
from pathlib import Path

import ollama_local  # même dossier ; ajoute aussi la racine du projet au chemin d'import

SCRIPTS = Path(__file__).resolve().parent


def main():
    version = ollama_local.demarrer()
    if version is None:
        print("Ollama est introuvable : installe-le depuis https://ollama.com/download puis relance installer.bat.")
        return 1
    print(f"Ollama {version}", flush=True)
    for modele in ollama_local.modeles_manquants():
        print(f"Téléchargement de {modele} (plusieurs Go)...", flush=True)
        ollama_local.telecharger(modele)

    subprocess.run([sys.executable, str(SCRIPTS / "telecharger_voix.py")], check=True)
    subprocess.run([sys.executable, str(SCRIPTS / "check_kb.py")], check=True)
    # Les alertes (VRAM, débit) n'empêchent pas la démo ; seul un échec arrête l'installation.
    return subprocess.run([sys.executable, str(SCRIPTS / "check_env.py")]).returncode


if __name__ == "__main__":
    sys.exit(main())
