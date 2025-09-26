from __future__ import annotations

from urllib.parse import urlparse

SUPPORTED_STORES = {
    "amazon": "Amazon",
    "mercadolivre": "Mercado Livre",
    "awin": "AWIN",
}


def detect_store(url: str) -> str:
    parsed = urlparse(url.lower())
    host = parsed.netloc
    if "amazon" in host:
        return "amazon"
    if "mercadolivre" in host or "mlb" in parsed.path.lower():
        return "mercadolivre"
    if "awin" in host or "go.awin" in host:
        return "awin"
    return "generic"
