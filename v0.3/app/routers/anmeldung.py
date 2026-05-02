from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models import (
    Wettkampf, Personen, PersonenHasWettkampf, Riege, Mannschaft,
)
from views import render, flash

router = APIRouter(prefix="/anmeldung")


@router.get("/{wid}")
def show(request: Request, wid: int, db: Session = Depends(get_db),
         user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        flash(request, "error", "Wettkampf nicht gefunden.")
        return RedirectResponse("/tage", status_code=303)
    angemeldete = (
        db.query(PersonenHasWettkampf)
        .filter_by(Wettkampf_id=wid)
        .order_by(PersonenHasWettkampf.Startnummer)
        .all()
    )
    angemeldet_ids = {a.Personen_id for a in angemeldete}
    alle_personen = (
        db.query(Personen).order_by(Personen.Nachname, Personen.Vorname).all()
    )
    verfuegbar = [p for p in alle_personen if p.idPersonen not in angemeldet_ids]
    return render(request, db, "wettkampf/anmeldung.html",
                  wk=wk, angemeldete=angemeldete, verfuegbar=verfuegbar)


@router.post("/{wid}/add")
def add(request: Request, wid: int,
        Personen_id: int = Form(...),
        Startnummer: str = Form(""),
        Riege_id: str = Form(""),
        Mannschaft_id: str = Form(""),
        db: Session = Depends(get_db),
        user=Depends(require_user(("admin", "tisch")))):
    next_nr = int(Startnummer) if Startnummer else (
        (db.query(PersonenHasWettkampf)
           .filter_by(Wettkampf_id=wid).count()) + 1
    )
    db.add(PersonenHasWettkampf(
        Personen_id=Personen_id, Wettkampf_id=wid,
        Startnummer=next_nr,
        Riege_id=int(Riege_id) if Riege_id else None,
        Mannschaft_id=int(Mannschaft_id) if Mannschaft_id else None,
        Start_Status="Gemeldet",
    ))
    db.commit()
    flash(request, "success", "Person angemeldet.")
    return RedirectResponse(f"/anmeldung/{wid}", status_code=303)


@router.post("/{wid}/{pid}/update")
def update(request: Request, wid: int, pid: int,
           Startnummer: str = Form(""),
           Riege_id: str = Form(""),
           Mannschaft_id: str = Form(""),
           Start_Status: str = Form("Gemeldet"),
           Status_Grund: str = Form(""),
           db: Session = Depends(get_db),
           user=Depends(require_user(("admin", "tisch")))):
    a = db.get(PersonenHasWettkampf, (pid, wid))
    if a:
        a.Startnummer = int(Startnummer) if Startnummer else None
        a.Riege_id = int(Riege_id) if Riege_id else None
        a.Mannschaft_id = int(Mannschaft_id) if Mannschaft_id else None
        a.Start_Status = Start_Status
        a.Status_Grund = Status_Grund or None
        db.commit()
    return RedirectResponse(f"/anmeldung/{wid}", status_code=303)


@router.post("/{wid}/{pid}/delete")
def remove(request: Request, wid: int, pid: int,
           db: Session = Depends(get_db),
           user=Depends(require_user(("admin", "tisch")))):
    a = db.get(PersonenHasWettkampf, (pid, wid))
    if a:
        db.delete(a); db.commit()
        flash(request, "success", "Anmeldung entfernt.")
    return RedirectResponse(f"/anmeldung/{wid}", status_code=303)
