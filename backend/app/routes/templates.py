from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import SessionDep
from ..models import OfferTemplate
from ..services.offer_builder import ensure_default_template

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/", response_model=list[schemas.TemplateRead])
def list_templates(session: Session = SessionDep):
    ensure_default_template(session)
    templates = session.query(OfferTemplate).order_by(OfferTemplate.name.asc()).all()
    return [schemas.TemplateRead.model_validate(item) for item in templates]


@router.post("/", response_model=schemas.TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(payload: schemas.TemplateCreate, session: Session = SessionDep):
    existing = session.query(OfferTemplate).filter_by(slug=payload.slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug já em uso")
    template = OfferTemplate(**payload.model_dump())
    if template.is_default:
        session.query(OfferTemplate).update({OfferTemplate.is_default: False})
    session.add(template)
    session.commit()
    session.refresh(template)
    return schemas.TemplateRead.model_validate(template)


def _get_template(session: Session, template_id: int) -> OfferTemplate:
    template = session.query(OfferTemplate).filter_by(id=template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template não encontrado")
    return template


@router.put("/{template_id}", response_model=schemas.TemplateRead)
def update_template(template_id: int, payload: schemas.TemplateUpdate, session: Session = SessionDep):
    template = _get_template(session, template_id)
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("is_default"):
        session.query(OfferTemplate).filter(OfferTemplate.id != template.id).update({OfferTemplate.is_default: False})
    for key, value in update_data.items():
        setattr(template, key, value)
    session.commit()
    session.refresh(template)
    return schemas.TemplateRead.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, session: Session = SessionDep):
    template = _get_template(session, template_id)
    session.delete(template)
    session.commit()
    return None
