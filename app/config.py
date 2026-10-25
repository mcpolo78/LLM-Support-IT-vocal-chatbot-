"""Réglages, modifiables par variables d'environnement."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))

# 127.0.0.1 plutôt que localhost : sous Windows, localhost tente d'abord IPv6 et perd ~2 s par appel.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
if not OLLAMA_HOST.startswith("http"):
    OLLAMA_HOST = "http://" + OLLAMA_HOST
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")

# Contexte du LLM : 3 fiches complètes + consignes tiennent largement dans 4096 tokens.
NUM_CTX = int(os.environ.get("NUM_CTX", "4096"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.1"))
# Nombre de passages récupérés, puis nombre de fiches complètes envoyées au LLM.
TOP_K_CHUNKS = int(os.environ.get("TOP_K_CHUNKS", "8"))
TOP_FICHES = int(os.environ.get("TOP_FICHES", "3"))
# Sous ce score de similarité, une fiche n'est pas envoyée au LLM (à calibrer avec l'évaluation).
SEUIL_PERTINENCE = float(os.environ.get("SEUIL_PERTINENCE", "0.45"))
# Garde les modèles chargés en VRAM entre deux questions.
KEEP_ALIVE = os.environ.get("KEEP_ALIVE", "30m")

# Coordonnées du support, toujours données au LLM pour qu'il n'invente pas de numéro (cf. KB-018).
CONTACT_SUPPORT = (
    "Assistance téléphonique du lundi au vendredi de 8 h à 18 h au 01 00 00 42 42 ; "
    "portail d'assistance https://assistance.academie-exemple.fr pour ouvrir un ticket."
)

# Voix (étape 3)
# Transcription : "large-v3-turbo" (~1,5 Go de VRAM) fait 6 % d'erreurs sur les mots contre 8 à 11 %
# pour "small" (~0,7 Go), pour le même délai avant le premier son. Repasser à "small" si la VRAM manque.
STT_MODEL = os.environ.get("STT_MODEL", "large-v3-turbo")
# "auto" essaie le GPU puis bascule sur le CPU si CUDA n'est pas utilisable.
STT_DEVICE = os.environ.get("STT_DEVICE", "auto")
STT_BEAM = int(os.environ.get("STT_BEAM", "3"))
VOIX_DIR = Path(os.environ.get("VOIX_DIR", DATA_DIR / "voix"))
TTS_VOIX = os.environ.get("TTS_VOIX", "fr_FR-siwis-medium")
# Supérieur à 1 : diction plus lente.
TTS_LENTEUR = float(os.environ.get("TTS_LENTEUR", "1.0"))
