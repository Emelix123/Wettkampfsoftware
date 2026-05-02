from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import current_user
from database import get_db
from models import Wettkampf
from views import render

router = APIRouter()


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    active = (
        db.query(Wettkampf)
        .filter(Wettkampf.Status.in_(["Anmeldung", "Aktiv"]))
        .order_by(Wettkampf.Wettkampf_Tag_id.desc(), Wettkampf.Wettkampf_Nr)
        .limit(10)
        .all()
    )
    return render(request, db, "dashboard.html", active=active)
