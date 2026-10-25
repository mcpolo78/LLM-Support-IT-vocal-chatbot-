"""Évalue le chatbot sur les 30 questions de test.

Usage : python eval/run_eval.py [--limite N]
Écrit eval/resultats.json (détail) et eval/resultats.md (tableau).
"""
import argparse
import json
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402
from app.rag import MoteurRAG  # noqa: E402


def normaliser(texte):
    texte = unicodedata.normalize("NFKD", texte.lower())
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return texte.replace("’", "'").replace(" ", " ").replace(" ", " ")


def evaluer(q, r):
    attendues = set(q["fiches_attendues"])
    trouvees = [s.id for s in r.sources]
    recherche_ok = bool(attendues & set(trouvees)) if attendues else None
    citation_ok = bool(attendues & set(r.citees)) if attendues else None
    texte = normaliser(r.texte)
    faits = [f for f in q["faits_cles"] if normaliser(f) in texte]
    taux_faits = len(faits) / len(q["faits_cles"]) if q["faits_cles"] else 1.0
    action_ok = r.action == q["comportement"]
    reussi = action_ok and recherche_ok is not False and taux_faits >= 0.5
    return {
        "id": q["id"], "style": q["style"], "question": q["question"],
        "attendu": q["comportement"], "obtenu": r.action, "action_ok": action_ok,
        "fiches_attendues": sorted(attendues), "fiches_trouvees": trouvees, "recherche_ok": recherche_ok,
        "citees": r.citees, "citation_ok": citation_ok,
        "faits_trouves": faits, "faits_manquants": [f for f in q["faits_cles"] if f not in faits],
        "taux_faits": round(taux_faits, 2), "reussi": reussi,
        "duree_ms": r.duree_totale_ms, "reponse": r.texte,
    }


def pct(valeurs):
    valeurs = [v for v in valeurs if v is not None]
    return f"{100 * sum(valeurs) / len(valeurs):.0f} %" if valeurs else "n/a"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args()

    questions = [json.loads(l) for l in (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    questions = questions[: args.limite]
    moteur = MoteurRAG()
    moteur.prechauffer()  # charge les modèles en VRAM avant de chronométrer

    lignes = []
    for q in questions:
        r = moteur.repondre(q["question"])
        res = evaluer(q, r)
        lignes.append(res)
        etat = "OK " if res["reussi"] else "KO "
        print(f"{etat} {q['id']} {res['obtenu']:<14} faits {res['taux_faits']:.0%}  {res['duree_ms'] / 1000:.1f} s  {q['question'][:60]}")

    durees = sorted(l["duree_ms"] for l in lignes)
    synthese = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "llm": config.LLM_MODEL, "embeddings": config.EMBED_MODEL,
        "questions": len(lignes),
        "reussite": pct([l["reussi"] for l in lignes]),
        "recherche_fiche_top3": pct([l["recherche_ok"] for l in lignes]),
        "citation_bonne_fiche": pct([l["citation_ok"] for l in lignes]),
        "action_correcte": pct([l["action_ok"] for l in lignes]),
        "faits_cles_moyen": f"{100 * sum(l['taux_faits'] for l in lignes) / len(lignes):.0f} %",
        "reussite_oral": pct([l["reussi"] for l in lignes if l["style"] == "oral"]),
        "duree_mediane_s": round(durees[len(durees) // 2] / 1000, 1),
        "duree_max_s": round(durees[-1] / 1000, 1),
    }
    (ROOT / "eval" / "resultats.json").write_text(
        json.dumps({"synthese": synthese, "detail": lignes}, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# Résultats de l'évaluation ({synthese['date']})", "",
          f"LLM `{synthese['llm']}`, embeddings `{synthese['embeddings']}`, {synthese['questions']} questions.", "",
          "| Indicateur | Valeur |", "|---|---|"]
    md += [f"| {k.replace('_', ' ')} | {v} |" for k, v in synthese.items() if k not in ("date", "llm", "embeddings")]
    md += ["", "| Q | Réussi | Attendu | Obtenu | Fiches trouvées | Citées | Faits manquants | Durée |",
           "|---|---|---|---|---|---|---|---|"]
    for l in lignes:
        md.append(f"| {l['id']} | {'oui' if l['reussi'] else 'non'} | {l['attendu']} | {l['obtenu']} | "
                  f"{', '.join(l['fiches_trouvees'])} | {', '.join(l['citees'])} | "
                  f"{', '.join(l['faits_manquants'])} | {l['duree_ms'] / 1000:.1f} s |")
    (ROOT / "eval" / "resultats.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n" + "\n".join(f"{k:<22} {v}" for k, v in synthese.items()))


if __name__ == "__main__":
    main()
