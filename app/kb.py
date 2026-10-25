"""Lecture des fiches et découpage en passages pour l'indexation."""
import re
from dataclasses import dataclass, field

from . import config


@dataclass
class Fiche:
    id: str
    titre: str
    categorie: str
    mots_cles: str
    escalade: str
    corps: str
    passages: list = field(default_factory=list)


def _lire_entete(bloc):
    meta = {}
    for ligne in bloc.splitlines():
        cle, _, valeur = ligne.partition(":")
        meta[cle.strip()] = valeur.strip().strip("[]")
    return meta


def _decouper(fiche):
    """Un passage « résumé » (titre, mots clés, symptômes) puis un passage par section."""
    sections = re.split(r"\n(?=## )", fiche.corps)
    passages = [f"{fiche.titre}\nMots clés : {fiche.mots_cles}\n{sections[0].lstrip('# ').strip()}"]
    for section in sections[1:]:
        texte = section.replace("## ", "", 1).strip()
        if texte:
            passages.append(f"{fiche.titre}\n{texte}")
    return passages


def charger_fiches():
    fiches = {}
    for path in sorted(config.KB_DIR.glob("*.md")):
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", path.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        meta = _lire_entete(m.group(1))
        corps = m.group(2).strip()
        # La mention « fiche fictive » n'apporte rien au LLM.
        corps = re.sub(r"\n_Fiche fictive.*?_\s*$", "", corps, flags=re.S).strip()
        fiche = Fiche(meta["id"], meta["titre"], meta["categorie"], meta["mots_cles"],
                      meta.get("escalade", ""), corps)
        fiche.passages = _decouper(fiche)
        fiches[fiche.id] = fiche
    return fiches
