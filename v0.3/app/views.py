"""Zentrale Template-Engine + Render-Helper, damit alle Router die
gleiche Jinja2-Konfiguration und automatische Globals (user, now) bekommen."""
from datetime import datetime

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import current_user

templates = Jinja2Templates(directory="templates")


def flash(request: Request, kind: str, msg: str) -> None:
    bag = request.session.get("flash", [])
    bag.append([kind, msg])
    request.session["flash"] = bag


def render(request: Request, db: Session, name: str, **ctx) -> HTMLResponse:
    ctx.setdefault("user", current_user(request, db))
    ctx.setdefault("now", datetime.utcnow())
    return templates.TemplateResponse(request, name, ctx)
