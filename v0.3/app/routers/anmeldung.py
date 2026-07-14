from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request
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
def show(request: Request, wid: int,
         sort: str = Query("nr"),
         fverein: Optional[int] = Query(None),
         friege: Optional[int] = Query(None),
         db: Session = Depends(get_db),
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

    # Vereine der Angemeldeten (fuer den Filter)
    vereine = sorted(
        {a.person.verein for a in angemeldete if a.person.verein},
        key=lambda v: v.Kuerzel or v.Name,
    )

    # Filter: Verein / Riege (friege=0 -> ohne Riege)
    if fverein:
        angemeldete = [a for a in angemeldete if a.person.Verein_id == fverein]
    if friege is not None:
        if friege == 0:
            angemeldete = [a for a in angemeldete if a.Riege_id is None]
        else:
            angemeldete = [a for a in angemeldete if a.Riege_id == friege]

    # Sortierung
    if sort == "name":
        angemeldete.sort(key=lambda a: (a.person.Nachname.lower(), a.person.Vorname.lower()))
    elif sort == "verein":
        angemeldete.sort(key=lambda a: (
            (a.person.verein.Kuerzel or a.person.verein.Name).lower() if a.person.verein else "zzz",
            a.person.Nachname.lower(),
        ))
    elif sort == "riege":
        angemeldete.sort(key=lambda a: (
            a.Riege_id is None,
            a.riege.Bezeichnung.lower() if a.riege else "",
            a.Startnummer if a.Startnummer is not None else 10**9,
        ))
    else:  # "nr" (Default)
        angemeldete.sort(key=lambda a: (a.Startnummer is None,
                                        a.Startnummer if a.Startnummer is not None else 0))

    alle_personen = (
        db.query(Personen).order_by(Personen.Nachname, Personen.Vorname).all()
    )
    verfuegbar = [p for p in alle_personen if p.idPersonen not in angemeldet_ids]
    return render(request, db, "wettkampf/anmeldung.html",
                  wk=wk, angemeldete=angemeldete, verfuegbar=verfuegbar,
                  vereine=vereine, sort=sort, fverein=fverein, friege=friege)


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


@router.post("/{wid}/riege-bulk")
async def riege_bulk(request: Request, wid: int,
                     db: Session = Depends(get_db),
                     user=Depends(require_user(("admin", "tisch")))):
    """Weist mehreren (per Checkbox gewaehlten) Anmeldungen auf einmal eine
    Riege zu. Leere Riege = Zuordnung entfernen."""
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    form = await request.form()
    pids = [int(p) for p in form.getlist("pids") if str(p).isdigit()]
    riege_raw = str(form.get("Riege_id") or "").strip()
    back = str(form.get("back") or "")
    if not back.startswith("/anmeldung"):
        back = f"/anmeldung/{wid}"

    if not pids:
        flash(request, "error", "Keine Personen ausgewaehlt.")
        return RedirectResponse(back, status_code=303)

    riege = None
    if riege_raw:
        riege = db.get(Riege, int(riege_raw))
        if not riege or riege.Wettkampf_id != wid:
            flash(request, "error", "Riege gehoert nicht zu diesem Wettkampf.")
            return RedirectResponse(back, status_code=303)

    n = 0
    for pid in pids:
        a = db.get(PersonenHasWettkampf, (pid, wid))
        if a:
            a.Riege_id = riege.idRiege if riege else None
            n += 1
    db.commit()
    if riege:
        flash(request, "success", f"{n} Person(en) der Riege '{riege.Bezeichnung}' zugeordnet.")
    else:
        flash(request, "success", f"Riegen-Zuordnung bei {n} Person(en) entfernt.")
    return RedirectResponse(back, status_code=303)


@router.post("/{wid}/startnummern-vergeben")
def startnummern_vergeben(request: Request, wid: int,
                          db: Session = Depends(get_db),
                          user=Depends(require_user(("admin", "tisch")))):
    """Vergibt fuer alle Anmeldungen OHNE Startnummer (z.B. Trainer-Meldungen)
    automatisch die naechsten freien Nummern. Bestehende bleiben unveraendert."""
    offene = (
        db.query(PersonenHasWettkampf)
        .filter_by(Wettkampf_id=wid)
        .filter(PersonenHasWettkampf.Startnummer.is_(None))
        .join(Personen, Personen.idPersonen == PersonenHasWettkampf.Personen_id)
        .order_by(Personen.Nachname, Personen.Vorname)
        .all()
    )
    if not offene:
        flash(request, "info", "Alle Anmeldungen haben bereits eine Startnummer.")
        return RedirectResponse(f"/anmeldung/{wid}", status_code=303)
    for a in offene:
        a.Startnummer = _next_free_startnr(db, wid)
        db.flush()
    db.commit()
    flash(request, "success", f"{len(offene)} Startnummern vergeben.")
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
