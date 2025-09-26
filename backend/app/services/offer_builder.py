from __future__ import annotations

from typing import Any

from jinja2 import BaseLoader, Environment, Template, TemplateError
from sqlalchemy.orm import Session

from ..config import settings
from ..models import OfferTemplate, TransformationRule
from .headlines import headline_for
from .rules import apply_rules
from .shortener import local_short_link

JINJA_ENV = Environment(loader=BaseLoader(), autoescape=False, trim_blocks=True, lstrip_blocks=True)

DEFAULT_TEMPLATE_SLUG = "default-announcement"
DEFAULT_TEMPLATE_BODY = """{{ emoji }} {{ headline }}

🛍️ {{ title }}

{% if price_original and price %}💰 De <s>{{ price_original }}</s> por {{ price }}{% elif price %}💰 {{ price }}{% endif %}
{% if coupon %}🎟️ CUPOM: {{ coupon }}{% endif %}
{% for benefit in benefits %}
{{ benefit }}
{% endfor %}
{% for line in extra_lines %}
{{ line }}
{% endfor %}

👉 {{ short_url }}
"""


def ensure_default_template(session: Session) -> OfferTemplate:
    template = session.query(OfferTemplate).filter_by(slug=DEFAULT_TEMPLATE_SLUG).first()
    if template:
        return template
    template = OfferTemplate(
        name="Template padrão",
        slug=DEFAULT_TEMPLATE_SLUG,
        description="Estrutura padrão de anúncio",
        body=DEFAULT_TEMPLATE_BODY,
        is_default=True,
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def get_template_by_slug(session: Session, slug: str | None) -> OfferTemplate:
    if slug:
        template = session.query(OfferTemplate).filter_by(slug=slug).first()
        if template:
            return template
    template = session.query(OfferTemplate).filter_by(is_default=True).first()
    if template:
        return template
    return ensure_default_template(session)


def render_template(template_body: str, context: dict[str, Any]) -> str:
    try:
        template: Template = JINJA_ENV.from_string(template_body)
        return template.render(**context)
    except TemplateError as exc:
        raise ValueError(f"Erro ao renderizar template: {exc}")


def build_context(metadata: dict[str, Any], affiliate_url: str, coupon: str | None, overrides: dict[str, Any]) -> dict[str, Any]:
    emoji, headline = headline_for(metadata.get("title"))
    context = {
        "emoji": overrides.get("emoji", emoji),
        "headline": overrides.get("headline", headline),
        "title": metadata.get("title"),
        "store": metadata.get("store"),
        "image": metadata.get("image"),
        "price": metadata.get("price"),
        "price_original": metadata.get("price_original"),
        "benefits": metadata.get("benefits") or [],
        "raw_prices": metadata.get("raw_prices") or [],
        "affiliate_url": affiliate_url,
        "coupon": overrides.get("coupon") or coupon,
        "extra_lines": overrides.get("extra_lines", []),
    }
    for key, value in overrides.items():\n        context[key] = value
    return context


def build_offer_text(
    session: Session,
    metadata: dict[str, Any],
    affiliate_url: str,
    coupon: str | None,
    template_slug: str | None,
    overrides: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    template = get_template_by_slug(session, template_slug)
    context = build_context(metadata, affiliate_url, coupon, overrides)
    short_url = overrides.get("short_url") or local_short_link(affiliate_url)
    context.setdefault("short_url", short_url)

    rules = session.query(TransformationRule).all()
    apply_rules(rules, context, context["extra_lines"])

    text = render_template(template.body, context)
    return text.strip(), context

