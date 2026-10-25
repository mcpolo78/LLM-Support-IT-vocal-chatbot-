"""Télécharge la voix Piper et le modèle Whisper, puis vérifie la chaîne voix -> texte.

Usage : python scripts/telecharger_voix.py
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402


def main():
    config.VOIX_DIR.mkdir(parents=True, exist_ok=True)
    if not (config.VOIX_DIR / f"{config.TTS_VOIX}.onnx").exists():
        print(f"Téléchargement de la voix Piper {config.TTS_VOIX}...")
        subprocess.run([sys.executable, "-m", "piper.download_voices", config.TTS_VOIX,
                        "--download-dir", str(config.VOIX_DIR)], check=True)
    print(f"Voix Piper : {config.VOIX_DIR / (config.TTS_VOIX + '.onnx')}")

    from app.stt import Transcripteur
    from app.tts import Synthetiseur

    debut = time.time()
    stt = Transcripteur()  # télécharge le modèle Whisper au premier lancement
    print(f"Whisper {config.STT_MODEL} chargé sur {stt.device} ({stt.compute}) en {time.time() - debut:.1f} s")

    tts = Synthetiseur()
    phrase = "Bonjour, je n'arrive plus à me connecter au VPN depuis ce matin."
    debut = time.time()
    wav = tts.wav(phrase)
    print(f"Synthèse : {len(wav) / 1024:.0f} Ko en {(time.time() - debut) * 1000:.0f} ms")
    texte, duree, ms = stt.transcrire(wav)
    print(f"Transcription de {duree} s d'audio en {ms} ms : « {texte} »")


if __name__ == "__main__":
    main()
