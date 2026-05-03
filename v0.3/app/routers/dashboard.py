from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import current_user
from database import get_db
from models import (
    Wettkampf, WettkampfTag, Personen, EinzelErgebnis, PersonenHasWettkampf,
)
from views import render

router = APIRouter()


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    active = (
        db.query(Wettkampf)
        .join(WettkampfTag)
        .filter(Wettkampf.Status.in_(["Anmeldung", "Aktiv"]))
        .order_by(WettkampfTag.Wettkampf_Datum.desc(), Wettkampf.Wettkampf_Nr)
        .limit(10).all()
    )
    today_tage = (
        db.query(WettkampfTag)
        .filter(WettkampfTag.Wettkampf_Datum == date.today())
        .all()
    )
    upcoming_tage = (
        db.query(WettkampfTag)
        .filter(WettkampfTag.Wettkampf_Datum > date.today())
        .order_by(WettkampfTag.Wettkampf_Datum).limit(5).all()
    )
    stats = {
        "personen": db.query(Personen).count(),
        "wettkaempfe_aktiv": db.query(Wettkampf).filter(Wettkampf.Status == "Aktiv").count(),
        "wettkampftage": db.query(WettkampfTag).count(),
        "ergebnisse_offen": db.query(EinzelErgebnis).filter(
            EinzelErgebnis.Status.in_(["Offen", "In_Bewertung"])
        ).count(),
    }
    return render(request, db, "dashboard.html",
                  active=active, today_tage=today_tage,
                  upcoming_tage=upcoming_tage, stats=stats)
