"""Appels à l'API HTTP d'Ollama (embeddings et chat)."""
import json

import httpx

from . import config

_TIMEOUT = httpx.Timeout(300.0, connect=5.0)


def embed(textes):
    r = httpx.post(
        f"{config.OLLAMA_HOST}/api/embed",
        json={"model": config.EMBED_MODEL, "input": textes, "keep_alive": config.KEEP_ALIVE},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["embeddings"]


def _payload(messages, stream):
    return {
        "model": config.LLM_MODEL,
        "messages": messages,
        "stream": stream,
        "keep_alive": config.KEEP_ALIVE,
        "options": {"num_ctx": config.NUM_CTX, "temperature": config.TEMPERATURE},
    }


def chat(messages):
    r = httpx.post(f"{config.OLLAMA_HOST}/api/chat", json=_payload(messages, False), timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()["message"]["content"]


def chat_stream(messages):
    """Renvoie les morceaux de texte au fur et à mesure de la génération."""
    with httpx.stream(
        "POST", f"{config.OLLAMA_HOST}/api/chat", json=_payload(messages, True), timeout=_TIMEOUT
    ) as r:
        r.raise_for_status()
        for ligne in r.iter_lines():
            if not ligne:
                continue
            morceau = json.loads(ligne)
            texte = morceau.get("message", {}).get("content", "")
            if texte:
                yield texte
            if morceau.get("done"):
                break
