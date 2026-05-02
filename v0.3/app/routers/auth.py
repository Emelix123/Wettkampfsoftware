from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import login_user, logout_user, verify_password, update_last_login
from database import get_db
from models import User
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
    user = db.query(User).filter(User.username == username, User.is_active == 1).first()
    if not user or not verify_password(password, user.password_hash):
        return render(request, db, "login.html", error="Falscher Benutzername oder Passwort.")
    login_user(request, user)
    update_last_login(db, user)
    flash(request, "success", f"Willkommen, {user.username}!")
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=303)
