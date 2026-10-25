"""API du chatbot et page de chat.

Lancement : uvicorn app.api:app --port 8000   puis http://localhost:8000
"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from . import config
from .rag import MoteurRAG

STATIC = config.ROOT / "app" / "static"
moteur = None
vocal = None
erreur_voix = None


@asynccontextmanager
async def lifespan(_app):
    global moteur, vocal, erreur_voix
    moteur = MoteurRAG()
    moteur.prechauffer()
    try:
        from .voix import AssistantVocal

        vocal = AssistantVocal(moteur)
        vocal.prechauffer()
    except Exception as e:  # le chat texte reste disponible sans la voix
        erreur_voix = str(e)
        print(f"Voix désactivée : {erreur_voix}")
    yield


app = FastAPI(title="Support IT vocal", lifespan=lifespan)


class Tour(BaseModel):
    role: str
    content: str


class Question(BaseModel):
    question: str
    historique: list[Tour] = []


@app.get("/")
def page():
    return FileResponse(STATIC / "index.html")


@app.get("/api/sante")
def sante():
    voix = ({"stt": config.STT_MODEL, "stt_device": f"{vocal.stt.device} ({vocal.stt.compute})",
             "tts": config.TTS_VOIX} if vocal else {"erreur": erreur_voix})
    return {"llm": config.LLM_MODEL, "embeddings": config.EMBED_MODEL,
            "fiches": len(moteur.fiches), "passages": moteur.collection.count(), "voix": voix}


@app.post("/api/chat")
def chat(q: Question):
    r = moteur.repondre(q.question, [t.model_dump() for t in q.historique])
    return {"reponse": r.texte, "action": r.action, "citees": r.citees,
            "sources": [s.__dict__ for s in r.sources],
            "duree_recherche_ms": r.duree_recherche_ms, "duree_totale_ms": r.duree_totale_ms}


@app.post("/api/chat/flux")
def chat_flux(q: Question):
    """Réponse en streaming (Server-Sent Events), un événement JSON par ligne « data: »."""
    return _sse(moteur.repondre_flux(q.question, [t.model_dump() for t in q.historique]))


@app.post("/api/voix")
def voix(audio: UploadFile | None = File(None), question: str | None = Form(None),
         historique: str = Form("[]")):
    """Question à l'oral (fichier audio) ou à l'écrit (champ question), réponse en texte et en audio (SSE)."""
    if vocal is None:
        raise HTTPException(503, f"voix indisponible : {erreur_voix}")
    if audio is None and not question:
        raise HTTPException(422, "envoyer un fichier audio ou une question")
    donnees = audio.file.read() if audio is not None else None
    return _sse(vocal.repondre(donnees, question, json.loads(historique)))


def _sse(evenements):
    def flux():
        for ev in evenements:
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
    return StreamingResponse(flux(), media_type="text/event-stream")
