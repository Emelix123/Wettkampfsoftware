import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import settings
from auth import ensure_default_admin
from csrf import csrf_dep, install_template_global
from routers import (
    auth as auth_router,
    dashboard, admin, wettkampftag, wettkampf, personen,
    anmeldung, eingabe, live, export,
)
from views import templates


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Startup: wartet bis 90s auf die DB und legt dann den Default-Admin an.
    Faengt JEDEN Fehler ab (OperationalError, ProgrammingError vor dem
    Init-Script-Lauf, Network-Errors)."""
    last_err = None
    for attempt in range(1, 91):
        try:
            ensure_default_admin()
            print(f"[startup] Admin-Setup OK (Versuch {attempt}).")
            break
        except Exception as e:
            last_err = e
            time.sleep(1)
    else:
        print(f"[startup] WARNUNG: Admin nach 90s nicht angelegt. "
              f"Letzter Fehler: {type(last_err).__name__}: {last_err}")
        print("[startup] Manuell: docker compose exec app python create_admin.py")
    yield


app = FastAPI(
    title="Wettkampfsoftware", version="0.3.0",
    lifespan=lifespan,
    dependencies=[Depends(csrf_dep)],   # CSRF auf allen Routen
)
install_template_global(templates)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    same_site="lax",
    https_only=False,
    max_age=settings.SESSION_MAX_AGE,  # auto-logout nach Idle-Zeit
)

app.mount("/static", StaticFiles(directory="static"), name="static")


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
