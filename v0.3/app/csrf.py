"""Einfacher CSRF-Schutz fuer Formulare.

Funktionsweise:
  * Beim 1. Request bekommt die Session ein zufaelliges Token.
  * In jedes <form method="post"> wird via {{ csrf_input(request) }} ein
    <input type="hidden" name="_csrf" value="..."> eingefuegt.
  * csrf_dep (FastAPI-Dependency, global registriert) prueft bei jedem
    POST/PUT/PATCH/DELETE ob das gesendete _csrf-Feld zum Session-Token passt.
  * GETs sind ausgenommen, /static auch.

Der Token rotiert nicht pro Request — er wechselt nur bei neuer Session.
Das ist OK fuer eine intranet-App und vermeidet Probleme mit mehreren
parallel offenen Forms (z.B. Tisch-Eingabe).
"""
import secrets

from fastapi import HTTPException, Request

CSRF_FIELD = "_csrf"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_or_create_token(session: dict) -> str:
    tok = session.get("csrf_token")
    if not tok:
        tok = secrets.token_urlsafe(32)
        session["csrf_token"] = tok
    return tok


async def csrf_dep(request: Request) -> None:
    # Token immer sicherstellen — auch bei GETs, damit das naechste Form
    # schon einen Token hat.
    expected = get_or_create_token(request.session)

    if request.method in SAFE_METHODS:
        return
    if request.url.path.startswith("/static"):
        return

    # Form lesen — Starlette cached das auf request._form, sodass die
    # eigentliche Route via await request.form() bzw. Form(...) den
    # gleichen geparsten Body bekommt.
    try:
        form = await request.form()
        sent = form.get(CSRF_FIELD)
    except Exception:
        sent = None

    if not sent or sent != expected:
        raise HTTPException(
            status_code=403,
            detail="Sicherheitstoken (CSRF) ungueltig oder abgelaufen. "
                   "Bitte Seite neu laden und nochmal absenden.",
        )


def install_template_global(templates) -> None:
    """Macht csrf_input() in allen Templates verfuegbar."""
    from markupsafe import Markup

    def csrf_input(request: Request) -> str:
        token = get_or_create_token(request.session)
        return Markup(
            f'<input type="hidden" name="{CSRF_FIELD}" value="{token}">'
        )

    templates.env.globals["csrf_input"] = csrf_input
