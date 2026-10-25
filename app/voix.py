"""Assistant vocal : audio de la question -> transcription -> RAG en streaming -> audio phrase par phrase."""
import base64
import time

from .tts import DecoupeurPhrases, texte_pour_oral


class AssistantVocal:
    def __init__(self, moteur):
        # Imports et chargements ici : sans les paquets de l'étape 3, le chat texte reste utilisable.
        from .stt import Transcripteur
        from .tts import Synthetiseur

        self.moteur = moteur
        self.stt = Transcripteur()
        self.tts = Synthetiseur()

    def prechauffer(self):
        self.tts.wav("Bonjour.")

    def repondre(self, audio=None, question=None, historique=()):
        """Générateur d'événements : transcription, puis ceux du RAG, entrecoupés d'événements audio.

        Les durées sont mesurées depuis la réception de la requête (donc juste après la fin de parole).
        """
        debut = time.time()
        if audio is not None:
            question, duree_audio, stt_ms = self.stt.transcrire(audio)
            yield {"type": "transcription", "texte": question, "duree_audio_s": duree_audio, "stt_ms": stt_ms}
            if not question:
                yield {"type": "fin", "action": "repondre", "citees": [], "premier_token_ms": None,
                       "duree_totale_ms": int((time.time() - debut) * 1000), "vide": True}
                return
        decoupeur, premier_audio, tts_ms = DecoupeurPhrases(), None, 0

        def audio_de(phrase):
            nonlocal premier_audio, tts_ms
            oral = texte_pour_oral(phrase)
            if not oral:
                return None
            t = time.time()
            wav = self.tts.wav(oral)
            tts_ms += int((time.time() - t) * 1000)
            if premier_audio is None:
                premier_audio = int((time.time() - debut) * 1000)
            return {"type": "audio", "texte": oral, "wav_b64": base64.b64encode(wav).decode()}

        for ev in self.moteur.repondre_flux(question, historique):
            if ev["type"] == "texte":
                yield ev
                for phrase in decoupeur.ajouter(ev["texte"]):
                    if (a := audio_de(phrase)):
                        yield a
            elif ev["type"] == "fin":
                for phrase in decoupeur.vider():
                    if (a := audio_de(phrase)):
                        yield a
                ev["premier_audio_ms"] = premier_audio
                ev["tts_ms"] = tts_ms
                ev["duree_totale_ms"] = int((time.time() - debut) * 1000)
                yield ev
            else:
                yield ev
