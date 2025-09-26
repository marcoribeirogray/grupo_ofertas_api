from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import SessionDep
from ..services.integrations import apply_affiliate
from ..services.metadata import fetch_metadata
from ..services.offer_builder import build_offer_text
from ..services.stores import detect_store

router = APIRouter(prefix="/api/offers", tags=["offers"])


@router.post("/preview", response_model=schemas.OfferPreviewResponse)
async def preview_offer(payload: schemas.OfferPreviewRequest, session: Session = SessionDep):
    store = payload.store or detect_store(payload.url)
    metadata = await fetch_metadata(payload.url, store)
    affiliate_url = apply_affiliate(payload.url, metadata["store"], session)
    coupon = payload.coupon
    text, context = build_offer_text(
        session=session,
        metadata=metadata,
        affiliate_url=affiliate_url,
        coupon=coupon,
        template_slug=payload.template_slug,
        overrides=payload.overrides,
    )

    return schemas.OfferPreviewResponse(
        title=context.get("title", metadata.get("title")),
        store=metadata.get("store"),
        affiliate_url=affiliate_url,
        short_url=context.get("short_url", affiliate_url),
        price=context.get("price") or metadata.get("price"),
        price_original=context.get("price_original") or metadata.get("price_original"),
        benefits=context.get("benefits", []),
        image=metadata.get("image"),
        text=text,
        metadata=metadata,
    )
