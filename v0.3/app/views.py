"""Zentrale Template-Engine + Render-Helper, damit alle Router die
gleiche Jinja2-Konfiguration und automatische Globals (user, now) bekommen."""
from datetime import datetime
from typing import Optional

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
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


def safe_delete(request: Request, db: Session, obj, name: Optional[str] = None) -> bool:
    """Loescht obj. Bei FK-Verletzung freundliche Fehlermeldung statt 500.
    Returns True bei Erfolg, False bei Konflikt (der User wird benachrichtigt)."""
    if obj is None:
        return False
    label = name or obj.__class__.__name__
    try:
        db.delete(obj)
        db.commit()
        flash(request, "success", f"{label} geloescht.")
        return True
    except IntegrityError:
        db.rollback()
        flash(
            request, "error",
            f"{label} kann nicht geloescht werden — wird noch verwendet "
            f"(z.B. von einem Wettkampf, einer Anmeldung oder einem Ergebnis). "
            f"Erst die Verwendung entfernen, dann nochmal versuchen."
        )
        return False
