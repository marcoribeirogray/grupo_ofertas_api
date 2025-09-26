from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, SessionLocal, engine
from .routes import auth, integrations, offers, rules, templates, web
from .services.integrations import ensure_default_integrations
from .services.offer_builder import ensure_default_template
from .services.users import ensure_default_admin

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Grupo Ofertas API",
    version="0.1.0",
    description="Plataforma configurável para geração de ofertas afiliadas",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie="grupo_session",
    https_only=False,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(integrations.router)
app.include_router(templates.router)
app.include_router(rules.router)
app.include_router(offers.router)
app.include_router(web.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        ensure_default_template(session)
        ensure_default_integrations(session)
        ensure_default_admin(session)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
