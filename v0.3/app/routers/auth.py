from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import (
    login_user, logout_user, verify_password, update_last_login,
    ensure_default_admin,
)
from database import get_db
from models import User
from services import ratelimit
from views import render, flash

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_form(request: Request, db: Session = Depends(get_db)):
    return render(request, db, "login.html", error=None)


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Rate-Limit-Key: User+IP. Damit ein Angreifer nicht durch User-Wechsel
    # entkommt, AND ein User nicht durch IP-Wechsel.
    client_ip = request.client.host if request.client else "?"
    rl_key = f"{username}@{client_ip}"

    blocked, wait = ratelimit.is_blocked(rl_key)
    if blocked:
        return render(request, db, "login.html",
                      error=f"Zu viele Fehlversuche. Bitte {wait}s warten.")

    user = db.query(User).filter(User.username == username, User.is_active == 1).first()
    # Lazy-Fallback: gibt es ueberhaupt noch keinen Admin (z.B. weil der
    # Startup-Hook beim ersten Boot nicht durchkam)? Dann jetzt anlegen.
    if not user and not db.query(User).filter(User.role == "admin").first():
        try:
            ensure_default_admin()
            user = db.query(User).filter(User.username == username, User.is_active == 1).first()
        except Exception as e:
            print(f"[login] Lazy-Admin-Anlage fehlgeschlagen: {e}")
    if not user or not verify_password(password, user.password_hash):
        ratelimit.record_fail(rl_key)
        return render(request, db, "login.html", error="Falscher Benutzername oder Passwort.")
    ratelimit.reset(rl_key)
    login_user(request, user)
    update_last_login(db, user)
    flash(request, "success", f"Willkommen, {user.username}!")
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=303)
