from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import SessionDep
from ..models import TransformationRule

router = APIRouter(prefix="/api/rules", tags=["rules"])


def _get_rule(session: Session, rule_id: int) -> TransformationRule:
    rule = session.query(TransformationRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada")
    return rule


@router.get("/", response_model=list[schemas.RuleRead])
def list_rules(session: Session = SessionDep):
    rules = session.query(TransformationRule).order_by(TransformationRule.created_at.desc()).all()
    return [schemas.RuleRead.model_validate(rule) for rule in rules]


@router.post("/", response_model=schemas.RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(payload: schemas.RuleBase, session: Session = SessionDep):
    rule = TransformationRule(**payload.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return schemas.RuleRead.model_validate(rule)


@router.put("/{rule_id}", response_model=schemas.RuleRead)
def update_rule(rule_id: int, payload: schemas.RuleUpdate, session: Session = SessionDep):
    rule = _get_rule(session, rule_id)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    session.commit()
    session.refresh(rule)
    return schemas.RuleRead.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, session: Session = SessionDep):
    rule = _get_rule(session, rule_id)
    session.delete(rule)
    session.commit()
    return None
