"""Transcription de la parole avec faster-whisper (GPU si possible, sinon CPU)."""
import io
import os
import site
import sys
import time
from pathlib import Path

import numpy as np

from . import config

# Le vocabulaire du support aide Whisper à bien écrire les sigles (ENT, VPN...).
VOCABULAIRE = (
    "Support informatique de l'académie : mot de passe, compte bloqué, ENT, EduConnect, messagerie, "
    "webmail, VPN, Wi-Fi, imprimante, vidéoprojecteur, visio, lecteur réseau, ticket."
)


def _dll_cuda_windows():
    """Sous Windows, rend visibles les DLL CUDA installées par pip (cuBLAS, cuDNN)."""
    if sys.platform != "win32":
        return
    for base in site.getsitepackages() + [site.getusersitepackages()]:
        for lib in ("cublas", "cudnn"):
            dossier = Path(base) / "nvidia" / lib / "bin"
            if dossier.is_dir():
                os.add_dll_directory(str(dossier))
                os.environ["PATH"] = str(dossier) + os.pathsep + os.environ.get("PATH", "")


class Transcripteur:
    def __init__(self):
        from faster_whisper import WhisperModel

        _dll_cuda_windows()
        if config.STT_DEVICE == "auto":
            essais = [("cuda", "int8_float16"), ("cpu", "int8")]
        else:
            essais = [(config.STT_DEVICE, "int8_float16" if config.STT_DEVICE == "cuda" else "int8")]
        erreurs = []
        for device, compute in essais:
            try:
                modele = WhisperModel(config.STT_MODEL, device=device, compute_type=compute)
                # Une demi-seconde de silence : vérifie que les DLL CUDA sont vraiment utilisables.
                segments, _ = modele.transcribe(np.zeros(8000, dtype=np.float32), language="fr", vad_filter=False)
                list(segments)
                self.modele, self.device, self.compute = modele, device, compute
                return
            except Exception as e:
                erreurs.append(f"{device}: {e}")
        raise RuntimeError("faster-whisper inutilisable : " + " | ".join(erreurs))

    def transcrire(self, audio):
        """audio : octets d'un fichier audio (webm, ogg, wav...) ou tableau numpy en 16 kHz.

        Renvoie (texte, durée de l'audio en s, durée de la transcription en ms).
        """
        debut = time.time()
        source = io.BytesIO(audio) if isinstance(audio, (bytes, bytearray)) else audio
        segments, info = self.modele.transcribe(
            source, language="fr", beam_size=config.STT_BEAM, vad_filter=True,
            initial_prompt=VOCABULAIRE, condition_on_previous_text=False,
        )
        texte = " ".join(s.text.strip() for s in segments).strip()
        return texte, round(info.duration, 2), int((time.time() - debut) * 1000)
