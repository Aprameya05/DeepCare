from __future__ import annotations

import os
from threading import Lock

from qdrant_client import QdrantClient


class QdrantClientWrapper:
    _instance: QdrantClient | None = None
    _lock = Lock()

    @classmethod
    def get_client(cls) -> QdrantClient:
        if cls._instance is not None:
            return cls._instance

        with cls._lock:
            if cls._instance is None:
                host = os.getenv("QDRANT_HOST", "localhost")
                port = int(os.getenv("QDRANT_PORT", "6333"))
                cls._instance = QdrantClient(host=host, port=port)
        return cls._instance
