"""Log parsing and chunking service."""
import logging
import re
from typing import Literal

from app.config import settings
from app.schemas import ChunkDTO, LogMetadata

logger = logging.getLogger(__name__)

LogSource = Literal["nginx", "app", "custom"]

NGINX_PATTERN = re.compile(
    r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} - .* \[.+\] "[A-Z]+ .+ HTTP/\d\.\d"'
)
APACHE_PATTERN = re.compile(
    r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} - .* \[.+\] "[A-Z]+ .+ HTTP/\d\.\d"'
)
SYSLOG_PATTERN = re.compile(
    r'^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\S+\s+\S+:'
)
APP_JSON_PATTERN = re.compile(r'^\s*\{.*"(level|timestamp|message)"')


def detect_source(content: str) -> LogSource:
    """Detect log format from content sample."""
    lines = content.split("\n")[:20]

    nginx_count = sum(1 for line in lines if NGINX_PATTERN.match(line))
    syslog_count = sum(1 for line in lines if SYSLOG_PATTERN.match(line))
    app_count = sum(1 for line in lines if APP_JSON_PATTERN.match(line))

    if nginx_count >= 3:
        return "nginx"
    if app_count >= 3:
        return "app"
    if syslog_count >= 3:
        return "custom"

    return "custom"


def chunk_lines(
    lines: list[str],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[ChunkDTO]:
    """Split lines into overlapping chunks."""
    chunk_size = chunk_size or settings.chunk_size_lines
    overlap = overlap or settings.chunk_overlap_lines

    if not lines:
        return []

    chunks: list[ChunkDTO] = []
    i = 0
    chunk_idx = 0
    step = max(1, chunk_size - overlap)

    while i < len(lines):
        end = min(i + chunk_size, len(lines))
        chunk_lines_slice = lines[i:end]
        chunk_text = "\n".join(chunk_lines_slice)

        if chunk_text.strip():
            chunks.append(
                ChunkDTO(
                    chunk_idx=chunk_idx,
                    line_start=i + 1,
                    line_end=end,
                    text=chunk_text,
                )
            )
            chunk_idx += 1

        i += step

    return chunks


def parse_log_content(
    content: str,
    source: LogSource | None = None,
) -> tuple[LogMetadata, list[ChunkDTO]]:
    """Parse log content into metadata and chunks."""
    if source is None:
        source = detect_source(content)

    lines = content.split("\n")
    lines = [line for line in lines if line.strip()]

    chunks = chunk_lines(lines)

    metadata = LogMetadata(
        source=source,
        total_lines=len(lines),
        total_chunks=len(chunks),
        byte_size=len(content.encode("utf-8")),
    )

    logger.info(
        f"Parsed log: source={source}, lines={len(lines)}, chunks={len(chunks)}"
    )

    return metadata, chunks


def validate_source(source: str) -> LogSource:
    """Validate and return source type."""
    if source in ("nginx", "app", "custom"):
        return source
    raise ValueError(f"Invalid source: {source}. Must be nginx, app, or custom.")
