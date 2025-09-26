from __future__ import annotations

from typing import Optional

from fastapi import Request
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return pwd_context.verify(plain_password, password_hash)


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        return None
    user = session.query(User).filter(User.email == normalized_email, User.is_active.is_(True)).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login_user(request: Request, user: User) -> None:
    request.session["user_id"] = user.id


def logout_user(request: Request) -> None:
    request.session.pop("user_id", None)
