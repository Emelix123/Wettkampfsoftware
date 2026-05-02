from datetime import datetime
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import User
import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def ensure_default_admin() -> None:
    """Beim Start: wenn noch kein admin existiert, lege einen mit den
    DEFAULT_ADMIN_*-Settings an."""
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "admin").first()
        if existing:
            return
        admin = User(
            username=settings.DEFAULT_ADMIN_USER,
            email=settings.DEFAULT_ADMIN_MAIL,
            password_hash=hash_password(settings.DEFAULT_ADMIN_PASS),
            role="admin",
            is_active=1,
        )
        db.add(admin)
        db.commit()
        print(
            f"[auth] Default-Admin angelegt: "
            f"{settings.DEFAULT_ADMIN_USER} / {settings.DEFAULT_ADMIN_PASS}"
        )
    finally:
        db.close()


# --- Session helpers ---------------------------------------------------------

def login_user(request: Request, user: User) -> None:
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role


def logout_user(request: Request) -> None:
    request.session.clear()


def current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get(User, uid)


def require_user(role: Optional[str | tuple[str, ...]] = None):
    """FastAPI dependency: stellt sicher, dass User eingeloggt ist
    und (optional) eine bestimmte Rolle hat. Andernfalls Redirect zu /login."""
    allowed: tuple[str, ...] = ()
    if isinstance(role, str):
        allowed = (role,)
    elif isinstance(role, tuple):
        allowed = role

    def _dep(request: Request, db: Session = Depends(get_db)) -> User:
        user = current_user(request, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/login"},
            )
        if allowed and user.role not in allowed and user.role != "admin":
            raise HTTPException(status_code=403, detail="Keine Berechtigung")
        # last_login einmal pro Request bumpen ist Overkill; lassen wir.
        return user

    return _dep


def update_last_login(db: Session, user: User) -> None:
    user.last_login = datetime.utcnow()
    db.commit()
