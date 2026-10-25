"""Test de bout en bout de la voix, sans micro.

Chaque question de test est lue par Piper, transcrite par Whisper, puis passe dans l'assistant
vocal complet. On mesure la qualité de transcription (taux d'erreur sur les mots), si la bonne
fiche est retrouvée à partir de la transcription, et la latence jusqu'au premier son.

Usage : python eval/test_voix.py [--limite N]
Écrit eval/resultats_voix.md. Une voix de synthèse est plus nette qu'un vrai micro :
c'est un test de non-régression, pas une mesure de la qualité en conditions réelles.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402
from app.rag import MoteurRAG  # noqa: E402
from app.voix import AssistantVocal  # noqa: E402
from eval.run_eval import normaliser  # noqa: E402


def erreur_mots(reference, hypothese):
    ref, hyp = normaliser(reference).split(), normaliser(hypothese).split()
    ref = [m.strip(",.?!;:'\"") for m in ref]
    hyp = [m.strip(",.?!;:'\"") for m in hyp]
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prec, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            prec, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prec + (r != h))
    return d[-1] / max(len(ref), 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args()
    questions = [json.loads(l) for l in (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    questions = questions[: args.limite]

    moteur = MoteurRAG()
    moteur.prechauffer()
    vocal = AssistantVocal(moteur)
    vocal.prechauffer()
    print(f"Whisper {config.STT_MODEL} sur {vocal.stt.device} ({vocal.stt.compute}), voix {config.TTS_VOIX}\n")

    lignes = []
    for q in questions:
        wav = vocal.tts.wav(q["question"])
        debut = time.time()
        transcription, stt_ms, sources, fin = "", 0, [], {}
        for ev in vocal.repondre(audio=wav):
            if ev["type"] == "transcription":
                transcription, stt_ms = ev["texte"], ev["stt_ms"]
            elif ev["type"] == "sources":
                sources = [s["id"] for s in ev["sources"]]
            elif ev["type"] == "fin":
                fin = ev
        attendues = set(q["fiches_attendues"])
        l = {
            "id": q["id"], "style": q["style"], "question": q["question"], "transcription": transcription,
            "wer": round(erreur_mots(q["question"], transcription), 2),
            "fiche_ok": bool(attendues & set(sources)) if attendues else None,
            "action_ok": fin.get("action") == q["comportement"],
            "stt_ms": stt_ms, "premier_audio_ms": fin.get("premier_audio_ms"),
            "total_ms": int((time.time() - debut) * 1000),
        }
        lignes.append(l)
        print(f"{q['id']} erreur mots {l['wer']:.0%}  stt {stt_ms} ms  1er son {l['premier_audio_ms']} ms  "
              f"fiche {'ok' if l['fiche_ok'] is not False else 'KO'}  « {transcription[:70]} »")

    def moy(cle, filtre=lambda l: True):
        vals = [l[cle] for l in lignes if filtre(l) and l[cle] is not None]
        return sum(vals) / len(vals) if vals else 0

    def pct(cle):
        vals = [l[cle] for l in lignes if l[cle] is not None]
        return f"{100 * sum(vals) / len(vals):.0f} %" if vals else "n/a"

    premiers = sorted(l["premier_audio_ms"] for l in lignes if l["premier_audio_ms"])
    synthese = {
        "questions": len(lignes),
        "erreur_mots_moyenne": f"{100 * moy('wer'):.0f} %",
        "erreur_mots_oral": f"{100 * moy('wer', lambda l: l['style'] == 'oral'):.0f} %",
        "bonne_fiche_apres_transcription": pct("fiche_ok"),
        "bonne_action": pct("action_ok"),
        "stt_moyen_ms": int(moy("stt_ms")),
        "premier_son_median_s": round(premiers[len(premiers) // 2] / 1000, 2) if premiers else None,
        "premier_son_max_s": round(premiers[-1] / 1000, 2) if premiers else None,
    }
    md = [f"# Test voix de bout en bout ({time.strftime('%Y-%m-%d %H:%M')})", "",
          f"Whisper `{config.STT_MODEL}` sur {vocal.stt.device}, voix Piper `{config.TTS_VOIX}`, LLM `{config.LLM_MODEL}`.", "",
          "| Indicateur | Valeur |", "|---|---|"]
    md += [f"| {k.replace('_', ' ')} | {v} |" for k, v in synthese.items()]
    md += ["", "| Q | Erreur mots | Fiche | Action | STT | 1er son | Transcription |", "|---|---|---|---|---|---|---|"]
    for l in lignes:
        md.append(f"| {l['id']} | {l['wer']:.0%} | {'ok' if l['fiche_ok'] is not False else 'KO'} | "
                  f"{'ok' if l['action_ok'] else 'KO'} | {l['stt_ms']} ms | {l['premier_audio_ms']} ms | {l['transcription']} |")
    (ROOT / "eval" / "resultats_voix.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n" + "\n".join(f"{k:<34} {v}" for k, v in synthese.items()))


if __name__ == "__main__":
    main()
