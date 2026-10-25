"""Vérifie la cohérence de la base de connaissances et du jeu de test.

Usage : python scripts/check_kb.py
Aucune dépendance externe.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"
QUESTIONS = ROOT / "eval" / "questions.jsonl"
CHAMPS = ["id", "titre", "categorie", "public", "mots_cles", "escalade"]
COMPORTEMENTS = {"repondre", "escalader", "refuser", "hors_perimetre"}


def lire_fiche(path):
    texte = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texte, re.S)
    if not m:
        raise ValueError("en-tête YAML absent")
    meta = {}
    for ligne in m.group(1).splitlines():
        cle, _, valeur = ligne.partition(":")
        meta[cle.strip()] = valeur.strip()
    return meta, m.group(2)


def main():
    erreurs = []
    fiches = {}
    for path in sorted(KB_DIR.glob("*.md")):
        try:
            meta, corps = lire_fiche(path)
        except ValueError as e:
            erreurs.append(f"{path.name} : {e}")
            continue
        for champ in CHAMPS:
            if not meta.get(champ):
                erreurs.append(f"{path.name} : champ « {champ} » manquant")
        fid = meta.get("id", "")
        if not path.name.startswith(fid):
            erreurs.append(f"{path.name} : le nom de fichier ne commence pas par {fid}")
        if fid in fiches:
            erreurs.append(f"{path.name} : id {fid} en double")
        fiches[fid] = corps

    for fid, corps in fiches.items():
        for ref in set(re.findall(r"KB-\d{3}", corps)):
            if ref not in fiches:
                erreurs.append(f"{fid} : renvoie vers {ref}, qui n'existe pas")

    questions = [json.loads(l) for l in QUESTIONS.read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        erreurs.append("questions.jsonl : id de question en double")
    for q in questions:
        if q["comportement"] not in COMPORTEMENTS:
            erreurs.append(f"{q['id']} : comportement inconnu {q['comportement']}")
        textes = []
        for fid in q["fiches_attendues"]:
            if fid not in fiches:
                erreurs.append(f"{q['id']} : fiche attendue {fid} inexistante")
            else:
                textes.append(fiches[fid].lower())
        # Chaque fait clé doit se trouver dans au moins une fiche attendue,
        # sinon le modèle ne peut pas le citer.
        if textes:
            for fait in q["faits_cles"]:
                if not any(fait.lower() in t for t in textes):
                    erreurs.append(f"{q['id']} : fait clé « {fait} » absent des fiches attendues")

    couvertes = {f for q in questions for f in q["fiches_attendues"]}
    for fid in fiches:
        if fid not in couvertes:
            erreurs.append(f"{fid} : aucune question de test ne couvre cette fiche")

    print(f"{len(fiches)} fiches, {len(questions)} questions")
    if erreurs:
        print(f"{len(erreurs)} problème(s) :")
        for e in erreurs:
            print("  -", e)
        sys.exit(1)
    print("OK : base de connaissances et jeu de test cohérents.")


if __name__ == "__main__":
    main()
