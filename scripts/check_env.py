"""Vérifie que la stack de l'étape 1 tourne sur ta machine.

Contrôles : version de Python, GPU NVIDIA et VRAM, serveur Ollama,
modèles installés, vitesse du LLM, embeddings, VRAM occupée.

Usage : python scripts/check_env.py
Variables optionnelles : OLLAMA_HOST, LLM_MODEL, EMBED_MODEL.
Aucune dépendance externe.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
if not OLLAMA.startswith("http"):
    OLLAMA = "http://" + OLLAMA
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")

# Budget VRAM : 8 Go au total, on garde ~1,5 Go pour faster-whisper (étape 3).
VRAM_MAX_ETAPE1_MO = 6500
DEBIT_MIN_TOKS = 20

resultats = []


def ok(nom, detail=""):
    resultats.append(("OK", nom, detail))
    print(f"[OK]    {nom} {detail}")


def warn(nom, detail=""):
    resultats.append(("ALERTE", nom, detail))
    print(f"[ALERTE] {nom} {detail}")


def ko(nom, detail=""):
    resultats.append(("ÉCHEC", nom, detail))
    print(f"[ÉCHEC] {nom} {detail}")


def api(chemin, payload=None, timeout=300):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        OLLAMA + chemin, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def vram_utilisee():
    if not shutil.which("nvidia-smi"):
        return None
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True,
    ).stdout.strip().splitlines()
    return int(out[0]) if out else None


def check_python():
    v = sys.version_info
    if v >= (3, 10):
        ok("Python", f"{v.major}.{v.minor}.{v.micro}")
    else:
        ko("Python", f"{v.major}.{v.minor} trouvé, 3.10 ou plus requis")


def check_gpu():
    if not shutil.which("nvidia-smi"):
        ko("GPU", "nvidia-smi introuvable : installe ou mets à jour le pilote NVIDIA")
        return
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True,
    ).stdout.strip()
    nom, total, utilise, pilote = [x.strip() for x in out.splitlines()[0].split(",")]
    ok("GPU", f"{nom}, {total} Mo de VRAM, {utilise} Mo déjà utilisés, pilote {pilote}")
    # Les modèles qu'Ollama garde chargés d'un lancement précédent ne comptent pas comme « pris ».
    autres = int(utilise) - vram_ollama()
    if autres > 1000:
        warn("VRAM au repos", f"{autres} Mo pris par d'autres programmes : ferme les jeux, navigateurs gourmands, etc.")


def vram_ollama():
    """VRAM (Mo) occupée par les modèles déjà chargés dans Ollama, 0 s'il ne répond pas."""
    try:
        return int(sum(m.get("size_vram", 0) for m in api("/api/ps", timeout=5).get("models", [])) / 2**20)
    except (urllib.error.URLError, OSError):
        return 0


def check_ollama():
    try:
        v = api("/api/version", timeout=5)
    except (urllib.error.URLError, OSError) as e:
        ko("Ollama", f"injoignable sur {OLLAMA} ({e}). Lance l'application Ollama ou `ollama serve`.")
        return False
    ok("Ollama", f"version {v.get('version')} sur {OLLAMA}")
    return True


def check_modeles():
    noms = {m["name"] for m in api("/api/tags").get("models", [])}
    presents = True
    for modele in (LLM_MODEL, EMBED_MODEL):
        if modele in noms or f"{modele}:latest" in noms:
            ok("Modèle", modele)
        else:
            ko("Modèle", f"{modele} absent. Lance : ollama pull {modele}")
            presents = False
    return presents


def check_llm():
    prompt = (
        "Tu es l'assistant du support informatique d'une académie. Réponds en français, "
        "en trois étapes numérotées et courtes : un enseignant dit que son vidéoprojecteur "
        "affiche « pas de signal »."
    )
    debut = time.time()
    r = api("/api/generate", {
        "model": LLM_MODEL, "prompt": prompt, "stream": False,
        "options": {"num_ctx": 4096, "temperature": 0.2},
        "keep_alive": "10m",
    })
    total = time.time() - debut
    debit = r["eval_count"] / (r["eval_duration"] / 1e9)
    chargement = r.get("load_duration", 0) / 1e9
    detail = f"{debit:.1f} tokens/s, chargement {chargement:.1f} s, total {total:.1f} s"
    (ok if debit >= DEBIT_MIN_TOKS else warn)("Vitesse LLM", detail)
    print("\n--- Réponse du modèle ---\n" + r["response"].strip() + "\n-------------------------\n")


def cosinus(a, b):
    num = sum(x * y for x, y in zip(a, b))
    return num / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def check_embeddings():
    textes = [
        "J'ai oublié mon mot de passe",
        "Réinitialiser son mot de passe académique oublié",
        "Le vidéoprojecteur affiche pas de signal",
    ]
    debut = time.time()
    r = api("/api/embed", {"model": EMBED_MODEL, "input": textes, "keep_alive": "10m"})
    duree = time.time() - debut
    vecs = r["embeddings"]
    proche, loin = cosinus(vecs[0], vecs[1]), cosinus(vecs[0], vecs[2])
    detail = f"dimension {len(vecs[0])}, similarité proche {proche:.2f} > éloignée {loin:.2f}, {duree:.1f} s"
    (ok if proche > loin else ko)("Embeddings", detail)


def check_vram_finale():
    try:
        for m in api("/api/ps").get("models", []):
            vram = m.get("size_vram", 0) / 2**20
            taille = m.get("size", 0) / 2**20
            cpu = "" if vram >= taille * 0.99 else " (une partie tourne sur le CPU)"
            print(f"        chargé : {m['name']} {vram:.0f} Mo en VRAM{cpu}")
    except (urllib.error.URLError, OSError):
        pass
    utilise = vram_utilisee()
    if utilise is None:
        return
    detail = f"{utilise} Mo utilisés avec le LLM et les embeddings chargés"
    if utilise <= VRAM_MAX_ETAPE1_MO:
        ok("Budget VRAM", detail + " : il reste de la place pour la voix (étape 3)")
    else:
        warn("Budget VRAM", detail + f" : au-delà de {VRAM_MAX_ETAPE1_MO} Mo, il faudra "
             "passer les embeddings sur CPU ou réduire num_ctx")


def main():
    print(f"LLM : {LLM_MODEL} | embeddings : {EMBED_MODEL}\n")
    check_python()
    check_gpu()
    if check_ollama() and check_modeles():
        check_llm()
        check_embeddings()
        check_vram_finale()
    echecs = [r for r in resultats if r[0] == "ÉCHEC"]
    alertes = [r for r in resultats if r[0] == "ALERTE"]
    print(f"\nBilan : {len(resultats) - len(echecs) - len(alertes)} OK, "
          f"{len(alertes)} alerte(s), {len(echecs)} échec(s).")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
