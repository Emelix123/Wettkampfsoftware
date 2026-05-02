from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models import Personen, Verein
from views import render, flash, safe_delete

router = APIRouter(prefix="/personen")


@router.get("")
def list_personen(request: Request,
                  edit: Optional[int] = Query(None),
                  q: Optional[str] = Query(None),
                  db: Session = Depends(get_db),
                  user=Depends(require_user())):
    qry = db.query(Personen)
    if q:
        from sqlalchemy import or_
        like = f"%{q.strip()}%"
        qry = qry.filter(or_(Personen.Vorname.ilike(like),
                             Personen.Nachname.ilike(like)))
    items = qry.order_by(Personen.Nachname, Personen.Vorname).all()
    vereine = db.query(Verein).order_by(Verein.Kuerzel).all()
    return render(request, db, "wettkampf/personen.html",
                  items=items, vereine=vereine, edit_id=edit, q=q or "")


@router.post("/{pid}/update")
def update_person(request: Request, pid: int,
                  Vorname: str = Form(...), Nachname: str = Form(...),
                  Geburtsdatum: str = Form(""),
                  Verein_id: str = Form(""),
                  Geschlecht: str = Form(""),
                  db: Session = Depends(get_db),
                  user=Depends(require_user(("admin", "tisch")))):
    obj = db.get(Personen, pid)
    if obj:
        obj.Vorname = Vorname.strip(); obj.Nachname = Nachname.strip()
        obj.Geburtsdatum = date.fromisoformat(Geburtsdatum) if Geburtsdatum else None
        obj.Verein_id = int(Verein_id) if Verein_id else None
        obj.Geschlecht = Geschlecht or None
        db.commit()
        flash(request, "success", f"Person '{obj.Vorname} {obj.Nachname}' aktualisiert.")
    return RedirectResponse("/personen", status_code=303)


@router.post("")
def create_person(request: Request,
                  Vorname: str = Form(...), Nachname: str = Form(...),
                  Geburtsdatum: str = Form(""),
                  Verein_id: str = Form(""),
                  Geschlecht: str = Form(""),
                  db: Session = Depends(get_db),
                  user=Depends(require_user(("admin", "tisch")))):
    db.add(Personen(
        Vorname=Vorname.strip(), Nachname=Nachname.strip(),
        Geburtsdatum=date.fromisoformat(Geburtsdatum) if Geburtsdatum else None,
        Verein_id=int(Verein_id) if Verein_id else None,
        Geschlecht=Geschlecht or None,
    ))
    db.commit()
    flash(request, "success", f"Person '{Vorname} {Nachname}' angelegt.")
    return RedirectResponse("/personen", status_code=303)


@router.post("/{pid}/delete")
def delete_person(request: Request, pid: int,
                  db: Session = Depends(get_db),
                  user=Depends(require_user("admin"))):
    obj = db.get(Personen, pid)
    safe_delete(request, db, obj,
                name=f"Person '{obj.Vorname} {obj.Nachname}'" if obj else None)
    return RedirectResponse("/personen", status_code=303)
