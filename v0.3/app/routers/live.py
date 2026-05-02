"""Oeffentliche Live-Ansicht (kein Login noetig)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Wettkampf, WettkampfTag
from services.rangliste import einzel_rangliste_mit_geraeten, mannschaft_rangliste
from views import render

router = APIRouter(prefix="/live")


@router.get("")
def live_index(request: Request, db: Session = Depends(get_db)):
    tage = (
        db.query(WettkampfTag)
        .order_by(WettkampfTag.Wettkampf_Datum.desc())
        .limit(20).all()
    )
    return render(request, db, "live/index.html", tage=tage)


@router.get("/tag/{tid}")
def tag(request: Request, tid: int, db: Session = Depends(get_db)):
    tag = db.get(WettkampfTag, tid)
    if not tag:
        return RedirectResponse("/live", status_code=303)
    return render(request, db, "live/tag.html", tag=tag)


@router.get("/wettkampf/{wid}")
def wettkampf(request: Request, wid: int, db: Session = Depends(get_db)):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/live", status_code=303)
    return render(request, db, "live/wettkampf.html", wk=wk)


# HTMX-Partial: nur die Rangliste, alle 5 Sekunden gepollt
@router.get("/wettkampf/{wid}/rangliste")
def wettkampf_rangliste(request: Request, wid: int, db: Session = Depends(get_db)):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/live", status_code=303)
    einzel, geraete = einzel_rangliste_mit_geraeten(db, wid)
    teams = []
    if wk.Typ != "Einzel":
        teams = mannschaft_rangliste(db, wid, wk.Mannschaft_Groesse)
    return render(request, db, "live/_rangliste.html",
                  wk=wk, einzel=einzel, teams=teams, geraete=geraete)
