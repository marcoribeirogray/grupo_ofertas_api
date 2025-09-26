from __future__ import annotations

import json
from typing import Any, Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..dependencies import SessionDep, require_any_role
from ..models import IntegrationSetting, OfferTemplate, TransformationRule, User
from ..services.integrations import ensure_default_integrations, upsert_integration
from ..services.offer_builder import build_offer_text, ensure_default_template
from ..services.metadata import fetch_metadata
from ..services.stores import SUPPORTED_STORES, detect_store

router = APIRouter(tags=["web"])

templates = Jinja2Templates(directory="app/templates")

EditorUser = Annotated[User, Depends(require_any_role("editor"))]
AdminUser = Annotated[User, Depends(require_any_role("admin"))]


def _render(request: Request, template_name: str, context: dict[str, Any]) -> HTMLResponse:
    context.setdefault("user", getattr(request.state, "user", None))
    return templates.TemplateResponse(template_name, context)


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: Session = SessionDep,
    current_user: EditorUser,
):
    request.state.user = current_user
    template_count = session.query(OfferTemplate).count()
    rule_count = session.query(TransformationRule).count()
    integrations = session.query(IntegrationSetting).count()
    return _render(
        request,
        "dashboard.html",
        {
            "template_count": template_count,
            "rule_count": rule_count,
            "integration_count": integrations,
        },
    )


@router.get("/integrations", response_class=HTMLResponse)
async def integrations_page(
    request: Request,
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    ensure_default_integrations(session)
    integrations = session.query(IntegrationSetting).order_by(IntegrationSetting.label.asc()).all()
    return _render(
        request,
        "integrations.html",
        {
            "integrations": integrations,
            "stores": SUPPORTED_STORES,
            "message": request.query_params.get("message"),
        },
    )


@router.post("/integrations/{provider}")
async def update_integration_form(
    provider: str,
    request: Request,
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    form = await request.form()
    label = form.get("label") or provider.title()
    data: dict[str, Any] = {k: v for k, v in form.items() if k not in {"label", "csrf_token"}}
    upsert_integration(session, provider, label, data)
    return RedirectResponse(url="/integrations?message=IntegraÃ§Ã£o atualizada", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/templates", response_class=HTMLResponse)
async def templates_page(
    request: Request,
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    ensure_default_template(session)
    items = session.query(OfferTemplate).order_by(OfferTemplate.created_at.desc()).all()
    return _render(
        request,
        "templates.html",
        {
            "templates": items,
            "message": request.query_params.get("message"),
        },
    )


@router.post("/templates")
async def create_template_form(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    body: str = Form(...),
    description: str = Form(""),
    is_default: bool = Form(False),
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    template = OfferTemplate(name=name, slug=slug, body=body, description=description, is_default=is_default)
    if template.is_default:
        session.query(OfferTemplate).update({OfferTemplate.is_default: False})
    session.add(template)
    session.commit()
    return RedirectResponse(url="/templates?message=Template criado", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/templates/{template_id}/delete")
async def delete_template_form(
    template_id: int,
    request: Request,
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    template = session.query(OfferTemplate).filter_by(id=template_id).first()
    if template:
        session.delete(template)
        session.commit()
    return RedirectResponse(url="/templates?message=Template removido", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/offers", response_class=HTMLResponse)
async def offers_page(
    request: Request,
    session: Session = SessionDep,
    current_user: EditorUser,
):
    request.state.user = current_user
    ensure_default_template(session)
    templates_list = session.query(OfferTemplate).order_by(OfferTemplate.name).all()
    return _render(
        request,
        "offers.html",
        {
            "templates": templates_list,
            "preview": None,
            "message": request.query_params.get("message"),
        },
    )


@router.post("/offers", response_class=HTMLResponse)
async def offers_preview(
    request: Request,
    session: Session = SessionDep,
    current_user: EditorUser,
):
    request.state.user = current_user
    form = await request.form()
    url = form.get("url")
    if not url:
        return RedirectResponse(url="/offers?message=Informe%20a%20URL", status_code=status.HTTP_303_SEE_OTHER)
    coupon = form.get("coupon") or None
    template_slug = form.get("template_slug") or None

    store = form.get("store") or detect_store(url)
    metadata = await fetch_metadata(url, store)
    affiliate_url = upsert_affiliate_if_needed(url, metadata["store"], session)
    overrides: dict[str, Any] = {}
    headline = form.get("headline_override")
    if headline:
        overrides["headline"] = headline
    emoji = form.get("emoji_override")
    if emoji:
        overrides["emoji"] = emoji

    text, context = build_offer_text(
        session=session,
        metadata=metadata,
        affiliate_url=affiliate_url,
        coupon=coupon,
        template_slug=template_slug,
        overrides=overrides,
    )
    templates_list = session.query(OfferTemplate).order_by(OfferTemplate.name).all()
    return _render(
        request,
        "offers.html",
        {
            "templates": templates_list,
            "preview": {
                "text": text,
                "context": context,
                "affiliate_url": affiliate_url,
            },
        },
    )


@router.get("/rules", response_class=HTMLResponse)
async def rules_page(
    request: Request,
    session: Session = SessionDep,
    current_user: EditorUser,
):
    request.state.user = current_user
    return _render_rules(request, session, current_user, message=request.query_params.get("message"), error=request.query_params.get("error"))


@router.post("/rules")
async def create_rule(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    conditions_json: str = Form("{}"),
    actions_json: str = Form("{}"),
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    conditions, error = _parse_json_field(conditions_json, default={})
    actions, error_actions = _parse_json_field(actions_json, default={})
    error = error or error_actions
    if error:
        return _render_rules(
            request,
            session,
            current_user,
            error=error,
            form_data={
                "name": name,
                "description": description,
                "conditions_json": conditions_json,
                "actions_json": actions_json,
            },
        )

    rule = TransformationRule(name=name, description=description, conditions=conditions, actions=actions)
    session.add(rule)
    session.commit()
    return RedirectResponse(url="/rules?message=Regra criada", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/rules/{rule_id}/update")
async def update_rule(
    rule_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    conditions_json: str = Form("{}"),
    actions_json: str = Form("{}"),
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    rule = session.query(TransformationRule).filter_by(id=rule_id).first()
    if not rule:
        return RedirectResponse(url="/rules?error=Regra%20nÃ£o%20encontrada", status_code=status.HTTP_303_SEE_OTHER)

    conditions, error = _parse_json_field(conditions_json, default=rule.conditions or {})
    actions, error_actions = _parse_json_field(actions_json, default=rule.actions or {})
    error = error or error_actions
    if error:
        return _render_rules(
            request,
            session,
            current_user,
            error=error,
            edit_rule=rule,
            form_data={
                "name": name,
                "description": description,
                "conditions_json": conditions_json,
                "actions_json": actions_json,
            },
        )

    rule.name = name
    rule.description = description
    rule.conditions = conditions
    rule.actions = actions
    session.commit()
    session.refresh(rule)
    return RedirectResponse(url="/rules?message=Regra atualizada", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/rules/{rule_id}/delete")
async def delete_rule(
    rule_id: int,
    request: Request,
    session: Session = SessionDep,
    current_user: AdminUser,
):
    request.state.user = current_user
    rule = session.query(TransformationRule).filter_by(id=rule_id).first()
    if rule:
        session.delete(rule)
        session.commit()
    return RedirectResponse(url="/rules?message=Regra removida", status_code=status.HTTP_303_SEE_OTHER)


def _parse_json_field(raw: str, default: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    raw = (raw or "").strip()
    if not raw:
        return default, None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return default, f"Erro ao interpretar JSON: {exc.msg}"
    if not isinstance(value, dict):
        return default, "O conteÃºdo deve ser um objeto JSON"
    return value, None


def _serialize_rules(rules: list[TransformationRule]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for rule in rules:
        serialized.append(
            {
                "entity": rule,
                "conditions_json": json.dumps(rule.conditions or {}, indent=2, ensure_ascii=False),
                "actions_json": json.dumps(rule.actions or {}, indent=2, ensure_ascii=False),
            }
        )
    return serialized


def _render_rules(
    request: Request,
    session: Session,
    current_user: User,
    *,
    message: str | None = None,
    error: str | None = None,
    edit_rule: TransformationRule | None = None,
    form_data: dict[str, Any] | None = None,
) -> HTMLResponse:
    rules = session.query(TransformationRule).order_by(TransformationRule.created_at.desc()).all()
    allow_manage = (current_user.role or "").lower() == "admin"
    context = {
        "request": request,
        "user": current_user,
        "rules": _serialize_rules(rules),
        "message": message,
        "error": error,
        "can_manage": allow_manage,
        "form_data": form_data or {},
        "edit_rule_id": edit_rule.id if edit_rule else None,
    }
    return templates.TemplateResponse("rules.html", context)


def upsert_affiliate_if_needed(url: str, store: str, session: Session) -> str:
    from ..services.integrations import apply_affiliate

    return apply_affiliate(url, store, session)
