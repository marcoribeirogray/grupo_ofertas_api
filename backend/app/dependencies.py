from __future__ import annotations

from typing import Annotated, Callable, Iterable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .database import get_session
from .models import User

SessionDep = Annotated[Session, Depends(get_session)]


def get_optional_user(request: Request, session: SessionDep) -> User | None:
    user_id = request.session.get("user_id") if request.session else None
    if not user_id:
        return None
    user = session.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        request.session.pop("user_id", None)
    return user


def get_current_user(request: Request, session: SessionDep) -> User:
    user = get_optional_user(request, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    return user


UserDep = Annotated[User, Depends(get_current_user)]


def require_any_role(*roles: str) -> Callable[[Request, Session], User]:
    allowed = {role.lower() for role in roles}

    def dependency(user: User = Depends(get_current_user)) -> User:
        user_role = (user.role or "").lower()
        if "admin" in allowed or user_role == "admin" or not allowed:
            return user
        if user_role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
        return user

    return dependency
