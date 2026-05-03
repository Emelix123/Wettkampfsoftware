from datetime import date

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models import WettkampfTag
from views import render, flash, safe_delete

router = APIRouter(prefix="/tage")


@router.get("")
def list_tage(request: Request, db: Session = Depends(get_db),
              user=Depends(require_user())):
    items = db.query(WettkampfTag).order_by(WettkampfTag.Wettkampf_Datum.desc()).all()
    return render(request, db, "wettkampf/tage_liste.html", items=items)


@router.post("")
def create_tag(request: Request,
               Name: str = Form(...),
               Wettkampf_Datum: str = Form(...),
               Ort: str = Form(""),
               Veranstalter: str = Form(""),
               db: Session = Depends(get_db),
               user=Depends(require_user("admin"))):
    db.add(WettkampfTag(
        Name=Name.strip(),
        Wettkampf_Datum=date.fromisoformat(Wettkampf_Datum),
        Ort=Ort or None, Veranstalter=Veranstalter or None,
    ))
    db.commit()
    flash(request, "success", f"Wettkampftag '{Name}' angelegt.")
    return RedirectResponse("/tage", status_code=303)


@router.post("/{tid}/update")
def update_tag(request: Request, tid: int,
               Name: str = Form(...),
               Wettkampf_Datum: str = Form(...),
               Ort: str = Form(""),
               Veranstalter: str = Form(""),
               db: Session = Depends(get_db),
               user=Depends(require_user("admin"))):
    obj = db.get(WettkampfTag, tid)
    if obj:
        obj.Name = Name.strip()
        obj.Wettkampf_Datum = date.fromisoformat(Wettkampf_Datum)
        obj.Ort = Ort or None
        obj.Veranstalter = Veranstalter or None
        db.commit()
        flash(request, "success", "Wettkampftag aktualisiert.")
    return RedirectResponse(f"/tage/{tid}", status_code=303)


@router.post("/{tid}/delete")
def delete_tag(request: Request, tid: int,
               db: Session = Depends(get_db),
               user=Depends(require_user("admin"))):
    obj = db.get(WettkampfTag, tid)
    safe_delete(request, db, obj, name=f"Wettkampftag '{obj.Name}'" if obj else None)
    return RedirectResponse("/tage", status_code=303)


@router.post("/{tid}/logo")
async def upload_logo(request: Request, tid: int,
                      logo: UploadFile = File(...),
                      db: Session = Depends(get_db),
                      user=Depends(require_user("admin"))):
    obj = db.get(WettkampfTag, tid)
    if obj:
        data = await logo.read()
        if len(data) > 2_000_000:
            flash(request, "error", "Logo darf max. 2 MB sein.")
        else:
            obj.Logo = data
            obj.Logo_MimeType = logo.content_type or "image/png"
            db.commit()
            flash(request, "success", "Logo gespeichert.")
    return RedirectResponse(f"/tage/{tid}", status_code=303)


@router.post("/{tid}/logo/delete")
def delete_logo(request: Request, tid: int,
                db: Session = Depends(get_db),
                user=Depends(require_user("admin"))):
    obj = db.get(WettkampfTag, tid)
    if obj:
        obj.Logo = None
        obj.Logo_MimeType = None
        db.commit()
    return RedirectResponse(f"/tage/{tid}", status_code=303)


@router.get("/{tid}")
def show_tag(request: Request, tid: int, db: Session = Depends(get_db),
             user=Depends(require_user())):
    tag = db.get(WettkampfTag, tid)
    if not tag:
        flash(request, "error", "Wettkampftag nicht gefunden.")
        return RedirectResponse("/tage", status_code=303)
    from models import Altersklasse
    altersklassen = db.query(Altersklasse).order_by(Altersklasse.Kuerzel).all()
    return render(request, db, "wettkampf/tag_detail.html",
                  tag=tag, altersklassen=altersklassen)
