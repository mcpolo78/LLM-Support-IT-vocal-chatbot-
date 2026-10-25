"""Ollama sur cette machine : vérifier qu'il répond, le démarrer, télécharger les modèles manquants."""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402


def version():
    """Version du serveur Ollama, ou None s'il ne répond pas."""
    try:
        with urllib.request.urlopen(config.OLLAMA_HOST + "/api/version", timeout=2) as r:
            return json.loads(r.read())["version"]
    except Exception:
        return None


def _commande():
    """L'application Ollama de Windows (serveur + icône), sinon la commande « ollama serve »."""
    appli = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama app.exe"
    if sys.platform == "win32" and appli.exists():
        return [str(appli)]
    ollama = shutil.which("ollama")
    return [ollama, "serve"] if ollama else None


def demarrer(attente=60):
    """Démarre Ollama s'il ne tourne pas. Renvoie sa version, ou None s'il reste injoignable."""
    if v := version():
        return v
    commande = _commande()
    if commande is None:
        return None
    if sys.platform == "win32":
        options = {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        options = {"start_new_session": True}
    subprocess.Popen(commande, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)
    fin = time.time() + attente
    while time.time() < fin:
        time.sleep(1)
        if v := version():
            return v
    return None


def modeles_manquants():
    with urllib.request.urlopen(config.OLLAMA_HOST + "/api/tags", timeout=5) as r:
        installes = {m["name"] for m in json.loads(r.read())["models"]}
    return [m for m in (config.LLM_MODEL, config.EMBED_MODEL)
            if m not in installes and f"{m}:latest" not in installes]


def telecharger(modele):
    """Télécharge un modèle par l'API d'Ollama (pas besoin de la commande ollama dans le PATH)."""
    requete = urllib.request.Request(
        config.OLLAMA_HOST + "/api/pull", data=json.dumps({"model": modele}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(requete, timeout=600) as r:
        for ligne in r:
            etat = json.loads(ligne)
            if "error" in etat:
                raise RuntimeError(f"{modele} : {etat['error']}")
            avance = f"{100 * etat.get('completed', 0) // etat['total']:3d} %" if etat.get("total") else ""
            print(f"\r  {etat.get('status', '')[:40]:40} {avance:5}", end="", flush=True)
    print()
