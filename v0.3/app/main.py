import time
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError
from starlette.middleware.sessions import SessionMiddleware

import settings
from auth import ensure_default_admin
from routers import (
    auth as auth_router,
    dashboard, admin, wettkampftag, wettkampf, personen,
    anmeldung, eingabe, live, export,
)

app = FastAPI(title="Wettkampfsoftware", version="0.3.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    for _ in range(30):
        try:
            ensure_default_admin()
            return
        except OperationalError:
            time.sleep(1)
    print("[startup] DB nicht erreichbar — Admin wird beim naechsten Login-Versuch angelegt.")


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    # Auth-Redirect via 303
    if exc.status_code == 303 and "Location" in (exc.headers or {}):
        return RedirectResponse(exc.headers["Location"], status_code=303)
    if exc.status_code == 403:
        return HTMLResponse(
            f"<h1>403 — Keine Berechtigung</h1><p>{exc.detail}</p>"
            f"<p><a href='/'>Zurueck zur Startseite</a></p>",
            status_code=403,
        )
    if exc.status_code == 404:
        return HTMLResponse(
            "<h1>404 — Nicht gefunden</h1><p><a href='/'>Zurueck</a></p>",
            status_code=404,
        )
    raise exc


app.include_router(auth_router.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(wettkampftag.router)
app.include_router(wettkampf.router)
app.include_router(personen.router)
app.include_router(anmeldung.router)
app.include_router(eingabe.router)
app.include_router(live.router)
app.include_router(export.router)


@app.get("/healthz")
def healthz():
    return {"ok": True}
