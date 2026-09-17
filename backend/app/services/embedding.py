"""Local embedding service using sentence-transformers."""
import hashlib
from functools import lru_cache

from app.config import settings

_model = None


def _get_model():
    """Lazy load embedding model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def _hash_fallback(text: str) -> list[float]:
    """Deterministic hash-based fallback vector for offline mode."""
    h = hashlib.sha384(text.encode()).digest()
    return [((b - 128) / 128.0) for b in h]


@lru_cache(maxsize=1000)
def _cached_embed(text: str) -> tuple[float, ...]:
    """Cached embedding computation."""
    try:
        model = _get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return tuple(embedding.tolist())
    except Exception:
        return tuple(_hash_fallback(text))


async def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text."""
    return list(_cached_embed(text))


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts."""
    try:
        model = _get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [e.tolist() for e in embeddings]
    except Exception:
        return [_hash_fallback(t) for t in texts]
