"""Synthèse vocale avec Piper, et adaptation du texte affiché pour qu'il se lise bien à voix haute."""
import io
import re
import wave

from . import config


class Synthetiseur:
    def __init__(self):
        from piper import PiperVoice, SynthesisConfig

        chemin = config.VOIX_DIR / f"{config.TTS_VOIX}.onnx"
        if not chemin.exists():
            raise FileNotFoundError(f"voix absente ({chemin}) : lance python scripts/telecharger_voix.py")
        self.voix = PiperVoice.load(chemin)
        self.reglages = SynthesisConfig(length_scale=config.TTS_LENTEUR)

    def wav(self, texte):
        tampon = io.BytesIO()
        with wave.open(tampon, "wb") as f:
            self.voix.synthesize_wav(texte, f, syn_config=self.reglages)
        return tampon.getvalue()


_LIAISONS = {1: "D'abord, ", 2: "Ensuite, ", 3: "Puis, ", 4: "Après ça, ", 5: "Enfin, "}
_KB = r"KB-\d{3}(?:\s*(?:,|et)\s*KB-\d{3})*"
_REMPLACEMENTS = [
    (re.compile(r"\s*[\[(](?:voir\s+(?:aussi\s+)?)?" + _KB + r"[\])]", re.I), ""),
    (re.compile(r"(?:\b(?:la|les)\s+(?:fiches?|procédures?)\s+)?" + _KB, re.I), "la fiche correspondante"),
    (re.compile(r"https?://\S+|\b[\w.-]+@[\w.-]+\.\w+\b"), "l'adresse affichée à l'écran"),
    (re.compile(r"`?\\\\[\w\\]+`?"), "le chemin affiché à l'écran"),
    (re.compile(r"\s*(?:>|→)\s*"), ", "),
    (re.compile(r"[*_`#]+"), ""),
    (re.compile(r"^\s*[-•]\s+", re.M), ""),
    # Une liste numérotée se dit plus naturellement avec des mots de liaison.
    (re.compile(r"^\s*(\d+)[.)]\s+(\w?)", re.M),
     lambda m: _LIAISONS.get(int(m.group(1)), "Ensuite, ") + m.group(2).lower()),
    (re.compile(r"(\d)\s*[×x]\s*(\d)"), r"\1 par \2"),
    (re.compile(r"\s*\+\s*"), " plus "),
    (re.compile(r"(\d)\s?h\b"), r"\1 heures"),
    (re.compile(r"(\d)\s?Go\b"), r"\1 gigaoctets"),
    (re.compile(r"(\d)\s?Mo\b"), r"\1 mégaoctets"),
    (re.compile(r"\s*:\s*$", re.M), "."),
    (re.compile(r"\s*\n\s*"), " "),
    (re.compile(r"[ \t]+"), " "),
]


def texte_pour_oral(texte):
    for motif, remplacement in _REMPLACEMENTS:
        texte = motif.sub(remplacement, texte)
    return texte.strip()


_FIN_PHRASE = re.compile(r"(?<=[.!?;])\s+|\n+")
# Pour la première phrase seulement : on accepte aussi de couper après une virgule ou deux-points.
_FIN_PREMIERE = re.compile(r"(?<=[.!?;:,])\s+|\n+")


class DecoupeurPhrases:
    """Reçoit le texte du LLM morceau par morceau et rend les phrases complètes.

    Les phrases trop courtes (« 1. ») sont regroupées avec la suivante pour éviter un débit haché.
    La première peut s'arrêter à une virgule, pour que la lecture commence au plus tôt.
    """

    def __init__(self, longueur_min=25):
        self.tampon = ""
        self.longueur_min = longueur_min
        self.premiere = True

    def ajouter(self, morceau):
        self.tampon += morceau
        phrases = []
        while True:
            m = None
            motif = _FIN_PREMIERE if self.premiere else _FIN_PHRASE
            for candidat in motif.finditer(self.tampon):
                if len(self.tampon[: candidat.start()].strip()) >= self.longueur_min:
                    m = candidat
                    break
            if not m:
                return phrases
            phrases.append(self.tampon[: m.start()].strip())
            self.tampon = self.tampon[m.end():]
            self.premiere = False

    def vider(self):
        reste, self.tampon = self.tampon.strip(), ""
        return [reste] if reste else []
