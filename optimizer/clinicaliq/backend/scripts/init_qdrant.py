from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from retrieval.collections import ensure_retrieval_collections  # noqa: E402


def main() -> None:
    created = ensure_retrieval_collections()
    print("Qdrant collections ready:")
    for name, was_created in created.items():
        state = "created" if was_created else "already_exists"
        print(f"- {name}: {state}")


if __name__ == "__main__":
    main()
