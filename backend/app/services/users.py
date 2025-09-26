from __future__ import annotations

from sqlalchemy.orm import Session

from ..config import settings
from ..models import User
from .auth import hash_password


def get_user_by_email(session: Session, email: str) -> User | None:
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return None
    return session.query(User).filter(User.email == normalized_email).first()


def ensure_default_admin(session: Session) -> None:
    email = (settings.default_admin_email or "").strip().lower()
    password = settings.default_admin_password or ""
    if not email or not password:
        return

    user = get_user_by_email(session, email)
    if user:
        return

    admin = User(
        email=email,
        full_name="Administrator",
        password_hash=hash_password(password),
        role=settings.default_admin_role or "admin",
        is_active=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
