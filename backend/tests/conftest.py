"""Pytest configuration and fixtures."""
import pytest


@pytest.fixture
def sample_nginx_log() -> str:
    """Sample nginx log content."""
    return """192.168.1.1 - - [17/Sep/2026:10:00:01 +0000] "GET /api/health HTTP/1.1" 200 15 "-" "curl/7.68.0"
192.168.1.2 - - [17/Sep/2026:10:00:02 +0000] "POST /api/logs/upload HTTP/1.1" 201 128 "-" "Mozilla/5.0"
192.168.1.3 - - [17/Sep/2026:10:00:05 +0000] "GET /api/logs HTTP/1.1" 200 4096 "-" "Mozilla/5.0"
192.168.1.1 - - [17/Sep/2026:10:00:10 +0000] "GET /api/health HTTP/1.1" 200 15 "-" "curl/7.68.0"
192.168.1.4 - - [17/Sep/2026:10:00:15 +0000] "POST /api/chat/query HTTP/1.1" 500 89 "-" "Mozilla/5.0"
"""


@pytest.fixture
def sample_app_log() -> str:
    """Sample application JSON log content."""
    return """{"timestamp": "2026-09-17T10:00:01Z", "level": "INFO", "message": "Server started"}
{"timestamp": "2026-09-17T10:00:02Z", "level": "DEBUG", "message": "Processing request"}
{"timestamp": "2026-09-17T10:00:03Z", "level": "ERROR", "message": "Database connection failed"}
{"timestamp": "2026-09-17T10:00:04Z", "level": "WARN", "message": "Retry attempt 1"}
"""


@pytest.fixture
def sample_lines() -> list[str]:
    """Sample log lines for chunking tests."""
    return [f"Line {i}: Sample log content here" for i in range(100)]
