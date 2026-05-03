from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
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


def _next_free_startnr(db: Session, wid: int) -> int:
    """Sucht die kleinste freie Startnummer >= 1 fuer einen Wettkampf."""
    used = {
        n for (n,) in db.query(PersonenHasWettkampf.Startnummer)
        .filter_by(Wettkampf_id=wid)
        .filter(PersonenHasWettkampf.Startnummer.isnot(None))
        .all()
    }
    n = 1
    while n in used:
        n += 1
    return n


@router.post("/{wid}/add")
def add(request: Request, wid: int,
        Personen_id: int = Form(...),
        Startnummer: str = Form(""),
        Riege_id: str = Form(""),
        Mannschaft_id: str = Form(""),
        db: Session = Depends(get_db),
        user=Depends(require_user(("admin", "tisch")))):
    if Startnummer.strip():
        try:
            next_nr = int(Startnummer)
        except ValueError:
            flash(request, "error", "Startnummer muss eine Zahl sein.")
            return RedirectResponse(f"/anmeldung/{wid}", status_code=303)
    else:
        next_nr = _next_free_startnr(db, wid)
    db.add(PersonenHasWettkampf(
        Personen_id=Personen_id, Wettkampf_id=wid,
        Startnummer=next_nr,
        Riege_id=int(Riege_id) if Riege_id else None,
        Mannschaft_id=int(Mannschaft_id) if Mannschaft_id else None,
        Start_Status="Gemeldet",
    ))
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig) if hasattr(e, "orig") else str(e)
        if "Startnr" in msg or "UQ_PhW_Startnr" in msg:
            flash(request, "error",
                  f"Startnummer {next_nr} ist in diesem Wettkampf bereits vergeben.")
        elif "PRIMARY" in msg:
            flash(request, "error", "Diese Person ist bereits angemeldet.")
        else:
            flash(request, "error", f"Anmeldung fehlgeschlagen: {msg[:120]}")
        return RedirectResponse(f"/anmeldung/{wid}", status_code=303)
    flash(request, "success", f"Person angemeldet (Startnummer {next_nr}).")
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
    if not a:
        return RedirectResponse(f"/anmeldung/{wid}", status_code=303)
    new_nr = None
    if Startnummer.strip():
        try:
            new_nr = int(Startnummer)
        except ValueError:
            flash(request, "error", "Startnummer muss eine Zahl sein.")
            return RedirectResponse(f"/anmeldung/{wid}", status_code=303)
    a.Startnummer = new_nr
    a.Riege_id = int(Riege_id) if Riege_id else None
    a.Mannschaft_id = int(Mannschaft_id) if Mannschaft_id else None
    a.Start_Status = Start_Status
    a.Status_Grund = Status_Grund or None
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig) if hasattr(e, "orig") else str(e)
        if "Startnr" in msg or "UQ_PhW_Startnr" in msg:
            flash(request, "error",
                  f"Startnummer {new_nr} ist in diesem Wettkampf bereits vergeben.")
        else:
            flash(request, "error", f"Update fehlgeschlagen: {msg[:120]}")
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
