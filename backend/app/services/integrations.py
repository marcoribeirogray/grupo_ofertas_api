from __future__ import annotations

from typing import Any
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse, quote

from sqlalchemy.orm import Session

from ..config import settings
from ..models import IntegrationSetting


def upsert_integration(session: Session, provider: str, label: str, data: dict[str, Any]) -> IntegrationSetting:
    integration = session.query(IntegrationSetting).filter_by(provider=provider).first()
    if integration is None:
        integration = IntegrationSetting(provider=provider, label=label, data=data)
        session.add(integration)
    else:
        integration.label = label
        integration.data = data
    session.commit()
    session.refresh(integration)
    return integration


def get_integration(session: Session, provider: str) -> IntegrationSetting | None:
    return session.query(IntegrationSetting).filter_by(provider=provider).first()


def get_integration_data(session: Session, provider: str) -> dict[str, Any]:
    integration = get_integration(session, provider)
    if integration:
        return integration.data or {}
    return {}


def ensure_default_integrations(session: Session) -> None:
    defaults = {
        "amazon": {
            "label": "Amazon Brasil",
            "data": {"tag": settings.default_amazon_tag or ""},
        },
        "mercadolivre": {
            "label": "Mercado Livre",
            "data": {
                "campaign_id": "",
                "seller_id": "",
            },
        },
        "awin": {
            "label": "AWIN",
            "data": {
                "deeplink_prefix": "",
                "source_id": settings.default_awin_source_id or "",
            },
        },
    }
    for provider, payload in defaults.items():
        if not get_integration(session, provider):
            upsert_integration(session, provider, payload["label"], payload["data"])


def apply_affiliate(url: str, store: str, session: Session) -> str:
    data = get_integration_data(session, store)
    if store == "amazon":
        tag = data.get("tag") or settings.default_amazon_tag
        if not tag:
            return url
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["tag"] = tag
        filtered = {k: v for k, v in query.items() if v is not None}
        new_query = urlencode(filtered)
        return urlunparse(parsed._replace(query=new_query))

    if store == "mercadolivre":
        campaign = data.get("campaign_id")
        if not campaign:
            return url
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["mldcid"] = campaign
        new_query = urlencode(query)
        return urlunparse(parsed._replace(query=new_query))

    if store == "awin":
        prefix = data.get("deeplink_prefix")
        if not prefix:
            return url
        encoded = quote(url, safe="")
        return f"{prefix}{encoded}"

    return url
