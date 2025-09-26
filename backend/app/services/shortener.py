from __future__ import annotations

import hashlib


def local_short_link(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"https://go.example/{digest}"
