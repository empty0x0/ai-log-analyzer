"""Tests for services layer."""
import pytest

from app.services.embedding import (
    EMBEDDING_DIM,
    clear_cache,
    get_embedding,
    get_embedding_dim,
    get_embeddings_batch,
)
from app.services.log_parser import (
    chunk_lines,
    detect_source,
    parse_log_content,
    validate_source,
)


class TestEmbedding:
    """Tests for embedding service."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @pytest.mark.asyncio
    async def test_get_embedding_returns_correct_dimension(self):
        """Embedding should return 384-dim vector."""
        text = "This is a test log entry"
        embedding = await get_embedding(text)

        assert len(embedding) == EMBEDDING_DIM
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_get_embedding_normalized(self):
        """Embedding should be L2 normalized (magnitude ~1)."""
        text = "Test log entry for normalization check"
        embedding = await get_embedding(text)

        magnitude = sum(x * x for x in embedding) ** 0.5
        assert 0.99 < magnitude < 1.01

    @pytest.mark.asyncio
    async def test_get_embedding_empty_string(self):
        """Empty string should return valid embedding via fallback."""
        embedding = await get_embedding("")

        assert len(embedding) == EMBEDDING_DIM

    @pytest.mark.asyncio
    async def test_get_embedding_deterministic(self):
        """Same text should return same embedding."""
        text = "Deterministic test"
        e1 = await get_embedding(text)
        clear_cache()
        e2 = await get_embedding(text)

        assert e1 == e2

    @pytest.mark.asyncio
    async def test_get_embeddings_batch(self):
        """Batch embedding should work correctly."""
        texts = ["First log", "Second log", "Third log"]
        embeddings = await get_embeddings_batch(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == EMBEDDING_DIM

    @pytest.mark.asyncio
    async def test_get_embeddings_batch_empty(self):
        """Empty batch should return empty list."""
        embeddings = await get_embeddings_batch([])
        assert embeddings == []

    def test_get_embedding_dim(self):
        """Should return correct dimension constant."""
        assert get_embedding_dim() == 384


class TestLogParser:
    """Tests for log parser service."""

    def test_detect_source_nginx(self, sample_nginx_log: str):
        """Should detect nginx format."""
        source = detect_source(sample_nginx_log)
        assert source == "nginx"

    def test_detect_source_app(self, sample_app_log: str):
        """Should detect app JSON format."""
        source = detect_source(sample_app_log)
        assert source == "app"

    def test_detect_source_unknown(self):
        """Unknown format should return custom."""
        content = "Random text\nMore random text\nNot a log"
        source = detect_source(content)
        assert source == "custom"

    def test_chunk_lines_basic(self, sample_lines: list[str]):
        """Should chunk lines correctly."""
        chunks = chunk_lines(sample_lines, chunk_size=10, overlap=2)

        assert len(chunks) > 0
        assert chunks[0].chunk_idx == 0
        assert chunks[0].line_start == 1
        assert chunks[0].line_end == 10

    def test_chunk_lines_overlap(self, sample_lines: list[str]):
        """Chunks should overlap correctly."""
        chunks = chunk_lines(sample_lines, chunk_size=10, overlap=2)

        if len(chunks) > 1:
            first_end = chunks[0].line_end
            second_start = chunks[1].line_start
            assert second_start < first_end

    def test_chunk_lines_empty(self):
        """Empty lines should return empty chunks."""
        chunks = chunk_lines([])
        assert chunks == []

    def test_chunk_lines_small_input(self):
        """Input smaller than chunk size should return single chunk."""
        lines = ["Line 1", "Line 2", "Line 3"]
        chunks = chunk_lines(lines, chunk_size=10, overlap=2)

        assert len(chunks) == 1
        assert chunks[0].line_start == 1
        assert chunks[0].line_end == 3

    def test_parse_log_content(self, sample_nginx_log: str):
        """Should parse log content into metadata and chunks."""
        metadata, chunks = parse_log_content(sample_nginx_log)

        assert metadata.source == "nginx"
        assert metadata.total_lines > 0
        assert metadata.total_chunks > 0
        assert metadata.byte_size > 0
        assert len(chunks) > 0

    def test_parse_log_content_with_source_override(self, sample_nginx_log: str):
        """Should respect source override."""
        metadata, _ = parse_log_content(sample_nginx_log, source="custom")

        assert metadata.source == "custom"

    def test_validate_source_valid(self):
        """Valid sources should pass."""
        assert validate_source("nginx") == "nginx"
        assert validate_source("app") == "app"
        assert validate_source("custom") == "custom"

    def test_validate_source_invalid(self):
        """Invalid source should raise error."""
        with pytest.raises(ValueError):
            validate_source("invalid")


class TestChunkDTO:
    """Tests for ChunkDTO schema."""

    def test_chunk_dto_creation(self):
        """Should create ChunkDTO correctly."""
        from app.schemas import ChunkDTO

        chunk = ChunkDTO(
            chunk_idx=0,
            line_start=1,
            line_end=10,
            text="Sample text",
        )

        assert chunk.chunk_idx == 0
        assert chunk.line_start == 1
        assert chunk.line_end == 10
        assert chunk.text == "Sample text"
        assert chunk.embedding is None

    def test_chunk_dto_with_embedding(self):
        """Should create ChunkDTO with embedding."""
        from app.schemas import ChunkDTO

        embedding = [0.1] * 384
        chunk = ChunkDTO(
            chunk_idx=0,
            line_start=1,
            line_end=10,
            text="Sample text",
            embedding=embedding,
        )

        assert chunk.embedding == embedding
