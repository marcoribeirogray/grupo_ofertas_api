from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..dependencies import SessionDep, get_optional_user
from ..services import auth

router = APIRouter(prefix="/auth", tags=["auth"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def login_form(request: Request, current_user=Depends(get_optional_user)):
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "user": None,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = SessionDep,
):
    user = auth.authenticate_user(session, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "user": None,
                "error": "Credenciais inválidas",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    auth.login_user(request, user)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout(request: Request):
    auth.logout_user(request)
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
