"""Lance la démo : vérifie Ollama et les modèles, démarre le serveur, puis ouvre la page.

Usage : python scripts/demarrer.py [--port 8000] [--sans-navigateur]
Sous Windows : double-clic sur demarrer.bat.
"""
import argparse
import json
import os
import sys
import threading
import time
import urllib.request
import webbrowser

import ollama_local  # même dossier ; ajoute aussi la racine du projet au chemin d'import

# installer.bat a déjà téléchargé Whisper : on ne contacte pas Hugging Face, la démo marche sans réseau.
os.environ.setdefault("HF_HUB_OFFLINE", "1")


def _sante(port):
    # 127.0.0.1 : sous Windows, localhost tente d'abord IPv6 et chaque essai raté coûte ~2 s.
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/sante", timeout=2) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _attendre_puis_ouvrir(port, url, ouvrir):
    debut = time.time()
    while (sante := _sante(port)) is None:
        time.sleep(0.5)
    voix = sante["voix"]
    if "erreur" in voix:
        print(f"Attention : voix désactivée ({voix['erreur']}).")
        print("Le chat écrit fonctionne. Si un modèle manque, lance installer.bat.")
    else:
        print(f"Voix : Whisper {voix['stt']} sur {voix['stt_device']}, Piper {voix['tts']}")
    print(f"\nPrêt en {time.time() - debut:.0f} s : {url}")
    print("Garde cette fenêtre ouverte pendant la démo. Ctrl+C pour arrêter.\n")
    if ouvrir:
        webbrowser.open(url)


def main():
    p = argparse.ArgumentParser(description="Lance la démo du support IT vocal.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--sans-navigateur", action="store_true", help="ne pas ouvrir la page")
    args = p.parse_args()
    url = f"http://127.0.0.1:{args.port}"

    if _sante(args.port):
        print(f"La démo tourne déjà : {url}")
        if not args.sans_navigateur:
            webbrowser.open(url)
        return 0

    print("Ollama...", end=" ", flush=True)
    version = ollama_local.demarrer()
    if version is None:
        print("injoignable.")
        print("Installe Ollama (https://ollama.com/download) ou lance l'application, puis recommence.")
        return 1
    print(f"OK (version {version})")
    manquants = ollama_local.modeles_manquants()
    if manquants:
        print(f"Modèles manquants : {', '.join(manquants)}. Lance installer.bat pour les télécharger.")
        return 1

    print("Chargement du LLM, des embeddings, de Whisper et de la voix (20 à 40 s)...")
    threading.Thread(target=_attendre_puis_ouvrir, args=(args.port, url, not args.sans_navigateur),
                     daemon=True).start()
    import uvicorn

    uvicorn.run("app.api:app", host="127.0.0.1", port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
