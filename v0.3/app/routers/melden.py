"""Trainer-Meldeportal.

Trainer (role=trainer, mit Verein_id) melden Teilnehmer ihres EIGENEN Vereins
fuer Wettkaempfe mit Status 'Anmeldung'. Gilt zusaetzlich der Meldeschluss
des Wettkampftags (wenn gesetzt).

Startnummern und Riegen-/Mannschafts-Zuteilung vergibt weiterhin der
Veranstalter unter /anmeldung — Trainer-Meldungen kommen ohne Startnummer an.
Admins koennen das Portal ebenfalls nutzen (Vereins-Auswahl via eigenes
Verein_id-Feld am User).
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models import (
    EinzelErgebnis, Personen, PersonenHasWettkampf, Verein, Wettkampf,
    WettkampfTag,
)
from services import audit
from views import render, flash

router = APIRouter(prefix="/melden")


def _trainer_verein(request: Request, user, db: Session) -> Verein | None:
    if not user.Verein_id:
        flash(request, "error",
              "Deinem Account ist kein Verein zugeordnet — bitte beim Admin melden.")
        return None
    return db.get(Verein, user.Verein_id)


def _meldung_offen(wk: Wettkampf) -> tuple[bool, str]:
    """Prueft Status + Meldeschluss. Returns (offen, grund_wenn_nicht)."""
    if wk.Status != "Anmeldung":
        return False, f"Wettkampf ist nicht in der Meldephase (Status: {wk.Status})."
    ms = wk.tag.Meldeschluss
    if ms and datetime.now() > ms:
        return False, f"Meldeschluss war am {ms.strftime('%d.%m.%Y %H:%M')}."
    return True, ""


@router.get("")
def index(request: Request, db: Session = Depends(get_db),
          user=Depends(require_user(("trainer",)))):
    verein = _trainer_verein(request, user, db)
    if not verein:
        return RedirectResponse("/", status_code=303)
    offene = (
        db.query(Wettkampf)
        .join(WettkampfTag, Wettkampf.Wettkampf_Tag_id == WettkampfTag.idWettkampf_Tag)
        .filter(Wettkampf.Status == "Anmeldung")
        .order_by(WettkampfTag.Wettkampf_Datum, Wettkampf.Wettkampf_Nr)
        .all()
    )
    # Anzahl eigener Meldungen pro Wettkampf
    counts: dict[int, int] = {}
    for wk in offene:
        counts[wk.idWettkampf] = (
            db.query(PersonenHasWettkampf)
            .join(Personen, Personen.idPersonen == PersonenHasWettkampf.Personen_id)
            .filter(PersonenHasWettkampf.Wettkampf_id == wk.idWettkampf,
                    Personen.Verein_id == verein.idVerein)
            .count()
        )
    return render(request, db, "melden/index.html",
                  verein=verein, offene=offene, counts=counts, jetzt=datetime.now())


@router.get("/{wid}")
def show(request: Request, wid: int, db: Session = Depends(get_db),
         user=Depends(require_user(("trainer",)))):
    verein = _trainer_verein(request, user, db)
    if not verein:
        return RedirectResponse("/", status_code=303)
    wk = db.get(Wettkampf, wid)
    if not wk:
        flash(request, "error", "Wettkampf nicht gefunden.")
        return RedirectResponse("/melden", status_code=303)
    offen, grund = _meldung_offen(wk)

    gemeldet = (
        db.query(PersonenHasWettkampf)
        .join(Personen, Personen.idPersonen == PersonenHasWettkampf.Personen_id)
        .filter(PersonenHasWettkampf.Wettkampf_id == wid,
                Personen.Verein_id == verein.idVerein)
        .order_by(Personen.Nachname, Personen.Vorname)
        .all()
    )
    gemeldet_ids = {a.Personen_id for a in gemeldet}
    verfuegbar = [
        p for p in (
            db.query(Personen)
            .filter(Personen.Verein_id == verein.idVerein)
            .order_by(Personen.Nachname, Personen.Vorname)
            .all()
        )
        if p.idPersonen not in gemeldet_ids
    ]
    return render(request, db, "melden/wettkampf.html",
                  wk=wk, verein=verein, gemeldet=gemeldet,
                  verfuegbar=verfuegbar, offen=offen, grund=grund)


@router.post("/{wid}/add")
def add(request: Request, wid: int,
        Personen_id: int = Form(...),
        db: Session = Depends(get_db),
        user=Depends(require_user(("trainer",)))):
    verein = _trainer_verein(request, user, db)
    wk = db.get(Wettkampf, wid)
    if not verein or not wk:
        return RedirectResponse("/melden", status_code=303)
    offen, grund = _meldung_offen(wk)
    if not offen:
        flash(request, "error", grund)
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    person = db.get(Personen, Personen_id)
    if not person or person.Verein_id != verein.idVerein:
        flash(request, "error", "Diese Person gehoert nicht zu deinem Verein.")
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    # Startnummer bleibt leer — vergibt der Veranstalter bei der Einteilung.
    db.add(PersonenHasWettkampf(
        Personen_id=Personen_id, Wettkampf_id=wid, Start_Status="Gemeldet",
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        flash(request, "error", "Diese Person ist bereits gemeldet.")
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    audit.log(db, user, "meldung.add", "PersonenHasWettkampf",
              f"{Personen_id}/{wid}",
              {"verein": verein.Kuerzel,
               "person": f"{person.Nachname}, {person.Vorname}"})
    flash(request, "success",
          f"{person.Vorname} {person.Nachname} gemeldet.")
    return RedirectResponse(f"/melden/{wid}", status_code=303)


@router.post("/{wid}/neu")
def neu(request: Request, wid: int,
        Vorname: str = Form(...), Nachname: str = Form(...),
        Geburtsdatum: str = Form(""), Geschlecht: str = Form(""),
        db: Session = Depends(get_db),
        user=Depends(require_user(("trainer",)))):
    """Neue Person im eigenen Verein anlegen UND direkt melden."""
    verein = _trainer_verein(request, user, db)
    wk = db.get(Wettkampf, wid)
    if not verein or not wk:
        return RedirectResponse("/melden", status_code=303)
    offen, grund = _meldung_offen(wk)
    if not offen:
        flash(request, "error", grund)
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    vorname, nachname = Vorname.strip(), Nachname.strip()
    if not vorname or not nachname:
        flash(request, "error", "Vor- und Nachname sind Pflicht.")
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    geb = None
    if Geburtsdatum.strip():
        try:
            geb = date.fromisoformat(Geburtsdatum.strip())
        except ValueError:
            flash(request, "error", "Geburtsdatum nicht lesbar (Format: JJJJ-MM-TT).")
            return RedirectResponse(f"/melden/{wid}", status_code=303)
    # Doppelte vermeiden: gleiche Person im gleichen Verein
    existing = (
        db.query(Personen)
        .filter(Personen.Verein_id == verein.idVerein,
                Personen.Vorname == vorname, Personen.Nachname == nachname,
                Personen.Geburtsdatum == geb)
        .first()
    )
    if existing:
        person = existing
    else:
        person = Personen(
            Vorname=vorname, Nachname=nachname, Geburtsdatum=geb,
            Verein_id=verein.idVerein,
            Geschlecht=Geschlecht if Geschlecht in ("m", "w", "d") else None,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
    db.add(PersonenHasWettkampf(
        Personen_id=person.idPersonen, Wettkampf_id=wid, Start_Status="Gemeldet",
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        flash(request, "error", "Diese Person ist bereits gemeldet.")
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    audit.log(db, user, "meldung.add_neu", "PersonenHasWettkampf",
              f"{person.idPersonen}/{wid}",
              {"verein": verein.Kuerzel,
               "person": f"{nachname}, {vorname}"})
    flash(request, "success", f"{vorname} {nachname} angelegt und gemeldet.")
    return RedirectResponse(f"/melden/{wid}", status_code=303)


@router.post("/{wid}/{pid}/remove")
def remove(request: Request, wid: int, pid: int,
           db: Session = Depends(get_db),
           user=Depends(require_user(("trainer",)))):
    verein = _trainer_verein(request, user, db)
    wk = db.get(Wettkampf, wid)
    if not verein or not wk:
        return RedirectResponse("/melden", status_code=303)
    offen, grund = _meldung_offen(wk)
    if not offen:
        flash(request, "error", f"Abmelden nicht mehr moeglich: {grund}")
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    a = db.get(PersonenHasWettkampf, (pid, wid))
    if not a or not a.person or a.person.Verein_id != verein.idVerein:
        flash(request, "error", "Meldung nicht gefunden oder nicht dein Verein.")
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    hat_ergebnisse = (
        db.query(EinzelErgebnis)
        .filter_by(Personen_id=pid, Wettkampf_id=wid)
        .count() > 0
    )
    if hat_ergebnisse:
        flash(request, "error",
              "Es existieren bereits Wertungen — Abmeldung nur ueber den Veranstalter.")
        return RedirectResponse(f"/melden/{wid}", status_code=303)
    name = f"{a.person.Vorname} {a.person.Nachname}"
    db.delete(a)
    db.commit()
    audit.log(db, user, "meldung.remove", "PersonenHasWettkampf",
              f"{pid}/{wid}", {"verein": verein.Kuerzel, "person": name})
    flash(request, "success", f"{name} abgemeldet.")
    return RedirectResponse(f"/melden/{wid}", status_code=303)
