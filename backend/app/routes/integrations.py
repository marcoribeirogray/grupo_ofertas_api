from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..dependencies import SessionDep
from ..models import IntegrationSetting
from ..services.integrations import get_integration, get_integration_data, upsert_integration

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/", response_model=list[schemas.IntegrationRead])
def list_integrations(session: Session = SessionDep):
    items = session.query(IntegrationSetting).all()
    return [schemas.IntegrationRead.model_validate(item) for item in items]


@router.get("/{provider}", response_model=schemas.IntegrationRead)
def get_integration_endpoint(provider: str, session: Session = SessionDep):
    integration = get_integration(session, provider)
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integração não encontrada")
    return schemas.IntegrationRead.model_validate(integration)


@router.put("/{provider}", response_model=schemas.IntegrationRead)
def update_integration(provider: str, payload: schemas.IntegrationUpdate, session: Session = SessionDep):
    data = payload.data
    label = payload.label
    integration = upsert_integration(session, provider, label, data)
    return schemas.IntegrationRead.model_validate(integration)
