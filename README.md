# Support IT vocal + chatbot (prototype local)

Prototype d'assistant de support informatique pour un contexte académique (personnels des établissements) : on pose sa question à l'écrit ou à la voix, l'assistant répond à partir d'une base de fiches de support, cite sa source, et propose d'ouvrir un ticket quand il ne sait pas.

Objectif : une démo qui tourne **entièrement en local** sur un portable RTX 4060 (8 Go de VRAM, 16 Go de RAM).

> Toutes les fiches de `kb/` sont **fictives** : adresses en `academie-exemple.fr`, numéro de téléphone factice. Elles imitent des procédures courantes de support, sans reprendre de documentation interne réelle.

## Lancer la démo (Windows)

1. Prérequis : pilote NVIDIA à jour, Python 3.10 ou plus récent, [Ollama](https://ollama.com/download).
2. **Une seule fois** : double-clic sur `installer.bat`. Il crée l'environnement Python `.venv`, installe les dépendances, télécharge les modèles (environ 10 Go en tout : LLM, embeddings, Whisper, voix) et lance les vérifications. Le relancer ne casse rien.
3. **À chaque démo** : double-clic sur `demarrer.bat`. Il démarre Ollama si besoin, charge les modèles (20 à 40 s) et ouvre http://127.0.0.1:8000. Garder la fenêtre ouverte pendant la démo.

Une fois installée, la démo fonctionne sans connexion Internet. Le déroulé conseillé, avec les questions à poser et les solutions de repli, est dans [DEMO.md](DEMO.md).

Hors Windows : `python scripts/demarrer.py` (options `--port`, `--sans-navigateur`).

## Plan

| Étape | Contenu | Statut |
|---|---|---|
| 1. Cadrage et base de connaissances | 21 fiches, 30 questions de test, vérification de la stack sur le PC | Fait (50 tokens/s, 5,4 Go de VRAM) |
| 2. Chatbot RAG en texte | FastAPI + Chroma + Ollama, citations, escalade vers ticket, évaluation | Fait : 93 à 97 % de réussite, 1er mot en 0,4 s |
| 3. Couche vocale | faster-whisper (STT) + Piper (TTS français), page web avec micro, moins de 3 s de latence | Fait : bonne fiche 100 % après transcription, 1er son en 1,4 s |
| 4. Packaging de la démo | Lanceur Windows (`installer.bat`, `demarrer.bat`), déroulé de démo ([DEMO.md](DEMO.md)), score final, pitch d'une page | Fait : prêt en 10 à 15 s, 93 à 97 % à l'écrit, bonne action 100 % à l'oral |

## Stack et budget VRAM

| Brique | Choix | VRAM estimée |
|---|---|---|
| LLM | `qwen2.5:7b` via Ollama (quantifié Q4_K_M), contexte 4096 | ~5 Go |
| Embeddings | `bge-m3` via Ollama (multilingue, bon en français) | ~1,2 Go |
| Transcription (étape 3) | faster-whisper `large-v3-turbo`, int8 | ~1,3 Go |
| Synthèse vocale (étape 3) | Piper, voix française, sur CPU | 0 |
| **Total** | | **6,8 Go sur 8 mesurés en pointe** |

Si la VRAM manque, on bascule les embeddings sur CPU (la base ne fait que 21 fiches, c'est rapide). Le LLM se change avec la variable `LLM_MODEL` (par exemple `qwen3:8b` ou `mistral:7b`) pour comparer.

## Contenu du dossier

```
kb/                     21 fiches de support (Markdown + en-tête YAML)
eval/questions.jsonl    30 questions de test (9 formulations orales, 3 escalades, 1 refus, 1 hors périmètre)
scripts/check_kb.py     vérifie la cohérence fiches / questions
scripts/check_env.py    vérifie GPU, Ollama, modèles, vitesse du LLM, embeddings, VRAM
app/kb.py               lecture des fiches, découpage en passages (résumé + une par section)
app/index.py            index vectoriel Chroma (reconstruit tout seul si les fiches changent)
app/rag.py              recherche, prompt, citations, action (répondre / escalader / refuser / hors périmètre)
app/api.py              API FastAPI + page de chat (app/static/index.html)
app/stt.py, app/tts.py  transcription (faster-whisper) et synthèse vocale (Piper)
app/voix.py             chaîne vocale : audio -> texte -> RAG -> audio phrase par phrase
eval/run_eval.py        score sur les 30 questions -> eval/resultats.md
eval/test_voix.py       test voix de bout en bout -> eval/resultats_voix.md
installer.bat           installation complète (venv, dépendances, modèles, vérifications)
demarrer.bat            lancement de la démo (scripts/demarrer.py, Ollama géré par scripts/ollama_local.py)
DEMO.md                 déroulé de la démo
```

Format d'une question de test :

```json
{"id": "Q23", "style": "ecrit", "question": "J'ai cliqué sur un lien...", "fiches_attendues": ["KB-016", "KB-001"],
 "comportement": "escalader", "faits_cles": ["Changez", "téléphone"]}
```

`comportement` vaut `repondre`, `escalader`, `refuser` ou `hors_perimetre`. `faits_cles` sont les éléments que la réponse doit contenir. Ils serviront au score automatique de l'étape 4.

## Tester l'étape 1 sur ton PC

### 1. Installer

**Windows**
1. Pilote NVIDIA à jour (GeForce Experience ou nvidia.com). Vérifie dans un terminal : `nvidia-smi`.
2. Python 3.10 ou plus récent : https://www.python.org/downloads/ (coche « Add python.exe to PATH »).
3. Ollama : https://ollama.com/download, puis lance l'application.

**Linux**
1. Pilote NVIDIA propriétaire, vérifie avec `nvidia-smi`.
2. `curl -fsSL https://ollama.com/install.sh | sh`

### 2. Télécharger les modèles (~6 Go)

```
ollama pull qwen2.5:7b
ollama pull bge-m3
```

### 3. Lancer les vérifications

Depuis ce dossier :

```
python scripts/check_kb.py
python scripts/check_env.py
```

Résultat attendu de `check_env.py` : tout en `[OK]`, au moins 20 tokens/s pour le LLM (une 4060 laptop fait en général 30 à 45 tokens/s sur un 7B en Q4), et moins de 6,5 Go de VRAM utilisés avec les deux modèles chargés.

**Copie-colle la sortie complète de `check_env.py` dans le fil** : elle me sert à régler l'étape 2 (taille de contexte, nombre de passages envoyés au modèle, embeddings sur GPU ou CPU).

## Étape 2 : lancer le chatbot

Ollama doit tourner (icône dans la barre des tâches). Depuis ce dossier :

```
python -m venv .venv
.venv\Scripts\activate          (Linux : source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.api:app --port 8000
```

Puis ouvre http://127.0.0.1:8000. Au premier lancement, l'index des fiches est construit automatiquement (quelques secondes).

Mesurer la qualité : `python eval/run_eval.py`, puis lire `eval/resultats.md`.

Résultats sur le PC (RTX 4060 laptop, 25/10/2026) :

| Version | Réussite | Bonne action | Bonne fiche citée | Recherche top 3 | 1er mot (API) |
|---|---|---|---|---|---|
| v1 | 73 % | 80 % | 19 % | 100 % | 4,8 s |
| v2 (consignes, lignes SOURCES/ACTION, fiche KB-021) | 97 % | 100 % | 93 % | 100 % | 4,8 s |
| v3 (Ollama sur 127.0.0.1 au lieu de localhost) | 93 % | 100 % | 97 % | 100 % | 0,4 s |

L'écart entre v2 et v3 vient de la variabilité du LLM : les deux échecs de v3 donnent la bonne procédure mais reformulent des faits clés (contrôle par mots exacts).

### Comment ça marche

1. La question est transformée en vecteur par bge-m3 et comparée aux 84 passages des fiches (Chroma, similarité cosinus).
2. Les 3 fiches les mieux classées sont envoyées **en entier** au LLM (elles sont courtes), sauf celles sous `SEUIL_PERTINENCE`.
3. Le LLM répond en suivant des consignes strictes : uniquement à partir des fiches, citation `[KB-xxx]`, 120 mots maximum (pour la voix), refus des demandes contraires à la sécurité, gestes d'urgence puis appel au support.
4. Il termine par deux lignes `SOURCES: KB-...` et `ACTION: ...` que l'API retire du texte : les sources deviennent des étiquettes, l'action un badge (et un bouton « Ouvrir un ticket » pour une escalade). Elles ne seront jamais lues à voix haute.

Réglages par variables d'environnement (voir `app/config.py`) : `LLM_MODEL`, `EMBED_MODEL`, `NUM_CTX`, `TOP_K_CHUNKS`, `TOP_FICHES`, `SEUIL_PERTINENCE`, `TEMPERATURE`.

API : `POST /api/chat` (réponse complète en JSON), `POST /api/chat/flux` (streaming SSE), `POST /api/voix` (audio ou texte en entrée, texte et audio en streaming SSE), `GET /api/sante`.

## Étape 3 : la voix

```
pip install -r requirements-voix.txt
python scripts/telecharger_voix.py      (voix Piper fr_FR-siwis-medium + modèle Whisper, puis un essai)
uvicorn app.api:app --port 8000
```

Sur la page, le bouton 🎙 démarre l'enregistrement, un second clic l'envoie. La case « Réponse vocale » fait aussi lire à voix haute les réponses aux questions tapées.

### Comment ça marche

1. Le navigateur enregistre la question (webm/opus) et l'envoie à `POST /api/voix`.
2. faster-whisper la transcrit (modèle `large-v3-turbo`, int8, sur GPU si CUDA est utilisable, sinon CPU), avec un vocabulaire du support en amorce (ENT, VPN, webmail...).
3. La transcription passe dans le même moteur RAG que le chat texte.
4. Dès qu'une phrase de la réponse est complète, elle est nettoyée pour l'oral (citations KB, adresses web, chemins réseau, `+`, `8 h`, `2 Go`...) puis synthétisée par Piper et envoyée au navigateur, qui la joue pendant que la suite se génère.
5. La page affiche le temps entre la fin de parole et le premier son.

`python eval/test_voix.py` rejoue les 30 questions sans micro : Piper les lit, Whisper les transcrit, et on mesure le taux d'erreur sur les mots, la fiche retrouvée, l'action et le délai jusqu'au premier son (`eval/resultats_voix.md`).

Résultats sur le PC (voix de synthèse, 30 questions) :

| Whisper | Erreur sur les mots | Bonne fiche | Bonne action | 1er son (médiane / max) | VRAM en pointe |
|---|---|---|---|---|---|
| `small` | 8 à 11 % | 100 % | 97 % | 1,4 s / 2,1 s | 5,9 Go |
| `large-v3-turbo` (par défaut) | 5 à 8 % | 100 % | 93 à 100 % | 1,4 à 1,5 s / 1,8 à 2,4 s | 6,8 Go |

Le premier son arrive 0,6 s après une question tapée, et 1,4 s environ après une question parlée (transcription comprise).

Installation : `av<19` est nécessaire, PyAV 19 casse faster-whisper 1.2. Sous Windows, Smart App Control peut bloquer une première fois une DLL de PyAV : relancer suffit.

Réglages : `STT_MODEL` (`large-v3-turbo`, `small`, `medium`), `STT_DEVICE` (`auto`, `cuda`, `cpu`), `STT_BEAM`, `TTS_VOIX`, `TTS_LENTEUR`.

## Étape 4 : score final

Avec les consignes finales (règle sur les demandes réservées à certains cas, note de relance), sur le PC :

| Passage | Réussite | Bonne action | Bonne fiche citée | Faits clés | Durée médiane |
|---|---|---|---|---|---|
| Écrit, passage 1 | 93 % | 100 % | 97 % | 86 % | 3,7 s |
| Écrit, passage 2 | 97 % | 97 % | 97 % | 89 % | 4,0 s |
| Voix (`test_voix.py`) | - | 100 % | 100 % (après transcription) | - | 1er son 1,47 s |

À l'oral, Whisper se trompe sur 5 % des mots (6 % sur les formulations orales). Les résultats varient de quelques points d'un passage à l'autre : le LLM n'est pas parfaitement déterministe, et Piper ne lit pas deux fois les questions de la même façon.

Points faibles connus :
- Q07 (augmentation du quota de messagerie) : la réponse dit bien que seules certaines fonctions y ont droit, mais oublie souvent la demande du chef de service, et l'action vaut parfois `refuser`.
- Les relances (« et si ça marche toujours pas ? ») sont repérées par `est_relance` dans `app/rag.py`, qui ajoute une consigne à la question. Le modèle donne alors la suite de la fiche et choisit `escalader`, mais il lui arrive de répéter d'abord les étapes déjà données.

## Confidentialité

Tout tourne sur la machine : Ollama, Chroma, Whisper et Piper. La télémétrie de Chroma est désactivée, et `demarrer.bat` empêche faster-whisper de contacter Hugging Face (`HF_HUB_OFFLINE=1`), car les modèles sont téléchargés à l'installation.
