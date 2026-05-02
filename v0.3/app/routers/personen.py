from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models import Personen, Verein
from views import render, flash

router = APIRouter(prefix="/personen")


@router.get("")
def list_personen(request: Request, db: Session = Depends(get_db),
                  user=Depends(require_user())):
    items = db.query(Personen).order_by(Personen.Nachname, Personen.Vorname).all()
    vereine = db.query(Verein).order_by(Verein.Kuerzel).all()
    return render(request, db, "wettkampf/personen.html", items=items, vereine=vereine)


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
    if obj:
        db.delete(obj); db.commit()
        flash(request, "success", "Person geloescht.")
    return RedirectResponse("/personen", status_code=303)
