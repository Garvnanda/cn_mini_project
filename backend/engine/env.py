"""Minimal .env loader (stdlib only). Real environment variables always win over the file."""

import os
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Path = DEFAULT) -> list[str]:
    """Read KEY=VALUE lines; skip blanks/comments; strip optional quotes. Returns keys it set."""
    if not path.exists():
        return []
    loaded = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip().removeprefix("export ").strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded
