"""Local embedding service using sentence-transformers with hash fallback."""
import hashlib
import logging
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
_model = None
_model_loaded = False
_model_error: str | None = None


def _get_model():
    """Lazy load embedding model."""
    global _model, _model_loaded, _model_error

    if _model is not None:
        return _model

    if _model_error is not None:
        raise RuntimeError(_model_error)

    try:
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        _model_loaded = True
        logger.info("Embedding model loaded successfully")
        return _model
    except Exception as e:
        _model_error = str(e)
        logger.warning(f"Failed to load embedding model: {e}. Using hash fallback.")
        raise


def _hash_fallback(text: str) -> list[float]:
    """Deterministic hash-based fallback vector (384-dim) for offline mode."""
    h = hashlib.sha384(text.encode("utf-8")).digest()
    return [((b - 128) / 128.0) for b in h]


def _normalize(vec: list[float]) -> list[float]:
    """L2 normalize vector."""
    norm = sum(x * x for x in vec) ** 0.5
    if norm == 0:
        return vec
    return [x / norm for x in vec]


@lru_cache(maxsize=1000)
def _cached_embed(text: str) -> tuple[float, ...]:
    """Cached embedding computation with fallback."""
    try:
        model = _get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return tuple(embedding.tolist())
    except Exception:
        return tuple(_normalize(_hash_fallback(text)))


async def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text (384-dim, normalized)."""
    if not text.strip():
        return _normalize(_hash_fallback(""))
    return list(_cached_embed(text[:8000]))


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts efficiently."""
    if not texts:
        return []

    texts = [t[:8000] if t else "" for t in texts]

    try:
        model = _get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [e.tolist() for e in embeddings]
    except Exception:
        return [_normalize(_hash_fallback(t)) for t in texts]


def is_model_loaded() -> bool:
    """Check if embedding model is loaded."""
    return _model_loaded


def get_embedding_dim() -> int:
    """Get embedding dimension."""
    return EMBEDDING_DIM


def clear_cache() -> None:
    """Clear embedding cache (for testing)."""
    _cached_embed.cache_clear()
