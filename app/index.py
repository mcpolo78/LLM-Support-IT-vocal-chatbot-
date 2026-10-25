"""Construit l'index vectoriel des fiches dans Chroma.

Usage : python -m app.index   (reconstruit l'index depuis kb/)
"""
import hashlib
import time

import chromadb

from . import config, ollama_client
from .kb import charger_fiches

COLLECTION = "fiches"


def _empreinte(fiches):
    h = hashlib.sha256(config.EMBED_MODEL.encode())
    for f in fiches.values():
        h.update("".join(f.passages).encode())
    return h.hexdigest()[:16]


def _client():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Chroma envoie par défaut des statistiques d'usage anonymes : rien ne doit sortir de la machine.
    return chromadb.PersistentClient(path=str(config.DATA_DIR / "chroma"),
                                     settings=chromadb.Settings(anonymized_telemetry=False))


def construire(fiches=None):
    fiches = fiches or charger_fiches()
    ids, docs, metas = [], [], []
    for f in fiches.values():
        for i, passage in enumerate(f.passages):
            ids.append(f"{f.id}#{i}")
            docs.append(passage)
            metas.append({"fiche": f.id, "titre": f.titre})
    # Embeddings d'abord : si Ollama ne répond pas, l'ancien index reste intact.
    debut = time.time()
    vecteurs = ollama_client.embed(docs)
    client = _client()
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        COLLECTION,
        embedding_function=None,
        metadata={"hnsw:space": "cosine", "empreinte": _empreinte(fiches)},
    )
    collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=vecteurs)
    print(f"Index construit : {len(fiches)} fiches, {len(ids)} passages, {time.time() - debut:.1f} s")
    return collection


def ouvrir():
    """Ouvre l'index, et le reconstruit si les fiches ou le modèle d'embeddings ont changé."""
    fiches = charger_fiches()
    client = _client()
    try:
        collection = client.get_collection(COLLECTION, embedding_function=None)
        if (collection.metadata or {}).get("empreinte") == _empreinte(fiches) and collection.count():
            return collection, fiches
    except Exception:
        pass
    return construire(fiches), fiches


if __name__ == "__main__":
    construire()
