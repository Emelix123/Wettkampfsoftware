"""Stammdaten-Verwaltung (nur Admin)."""
from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import require_user, hash_password
from database import get_db
from models import Verein, Altersklasse, Geraete, BerechnungsArt, User
from views import render, flash, safe_delete

router = APIRouter(prefix="/admin", dependencies=[Depends(require_user("admin"))])


@router.get("")
def admin_home(request: Request, db: Session = Depends(get_db)):
    return render(request, db, "admin/index.html",
                  vereine_count=db.query(Verein).count(),
                  ak_count=db.query(Altersklasse).count(),
                  geraete_count=db.query(Geraete).count(),
                  berechnung_count=db.query(BerechnungsArt).count(),
                  user_count=db.query(User).count())


@router.get("/audit")
def audit_view(request: Request, page: int = 1, db: Session = Depends(get_db)):
    from models import AuditLog
    PAGE = 100
    page = max(1, page)
    total = db.query(AuditLog).count()
    items = (
        db.query(AuditLog)
        .order_by(AuditLog.zeitpunkt.desc())
        .offset((page - 1) * PAGE).limit(PAGE).all()
    )
    pages = max(1, (total + PAGE - 1) // PAGE)
    return render(request, db, "admin/audit.html",
                  items=items, page=page, pages=pages, total=total)


@router.get("/backup")
def backup_view(request: Request, db: Session = Depends(get_db)):
    from models import WettkampfTag
    tage = (
        db.query(WettkampfTag)
        .order_by(WettkampfTag.Wettkampf_Datum.desc()).all()
    )
    return render(request, db, "admin/backup.html", tage=tage)


# ---------------- Vereine ----------------------------------------------------

@router.get("/vereine")
def vereine(request: Request, edit: Optional[int] = Query(None),
            db: Session = Depends(get_db)):
    items = db.query(Verein).order_by(Verein.Kuerzel).all()
    return render(request, db, "admin/vereine.html", items=items, edit_id=edit)


@router.post("/vereine")
def vereine_create(request: Request,
                   Kuerzel: str = Form(...), Name: str = Form(...),
                   Ort: str = Form(""),
                   db: Session = Depends(get_db)):
    db.add(Verein(Kuerzel=Kuerzel.strip(), Name=Name.strip(), Ort=(Ort or None)))
    db.commit()
    flash(request, "success", f"Verein '{Kuerzel}' angelegt.")
    return RedirectResponse("/admin/vereine", status_code=303)


@router.post("/vereine/{vid}/update")
def vereine_update(request: Request, vid: int,
                   Kuerzel: str = Form(...), Name: str = Form(...),
                   Ort: str = Form(""),
                   db: Session = Depends(get_db)):
    obj = db.get(Verein, vid)
    if obj:
        obj.Kuerzel = Kuerzel.strip(); obj.Name = Name.strip()
        obj.Ort = Ort or None
        db.commit()
        flash(request, "success", f"Verein '{obj.Kuerzel}' aktualisiert.")
    return RedirectResponse("/admin/vereine", status_code=303)


@router.post("/vereine/{vid}/delete")
def vereine_delete(request: Request, vid: int, db: Session = Depends(get_db)):
    obj = db.get(Verein, vid)
    safe_delete(request, db, obj, name=f"Verein '{obj.Kuerzel}'" if obj else None)
    return RedirectResponse("/admin/vereine", status_code=303)


# ---------------- Altersklassen ---------------------------------------------

@router.get("/altersklassen")
def altersklassen(request: Request, edit: Optional[int] = Query(None),
                  db: Session = Depends(get_db)):
    items = db.query(Altersklasse).order_by(Altersklasse.Kuerzel).all()
    return render(request, db, "admin/altersklassen.html", items=items, edit_id=edit)


@router.post("/altersklassen/{aid}/update")
def altersklassen_update(request: Request, aid: int,
                         Kuerzel: str = Form(...), Bezeichnung: str = Form(...),
                         Alter_Von: str = Form(""), Alter_Bis: str = Form(""),
                         Geschlecht: str = Form("alle"),
                         db: Session = Depends(get_db)):
    obj = db.get(Altersklasse, aid)
    if obj:
        obj.Kuerzel = Kuerzel.strip(); obj.Bezeichnung = Bezeichnung.strip()
        obj.Alter_Von = int(Alter_Von) if Alter_Von else None
        obj.Alter_Bis = int(Alter_Bis) if Alter_Bis else None
        obj.Geschlecht = Geschlecht
        db.commit()
        flash(request, "success", f"Altersklasse '{obj.Kuerzel}' aktualisiert.")
    return RedirectResponse("/admin/altersklassen", status_code=303)


@router.post("/altersklassen")
def altersklassen_create(request: Request,
                         Kuerzel: str = Form(...), Bezeichnung: str = Form(...),
                         Alter_Von: str = Form(""), Alter_Bis: str = Form(""),
                         Geschlecht: str = Form("alle"),
                         db: Session = Depends(get_db)):
    db.add(Altersklasse(
        Kuerzel=Kuerzel.strip(), Bezeichnung=Bezeichnung.strip(),
        Alter_Von=int(Alter_Von) if Alter_Von else None,
        Alter_Bis=int(Alter_Bis) if Alter_Bis else None,
        Geschlecht=Geschlecht,
    ))
    db.commit()
    flash(request, "success", f"Altersklasse '{Kuerzel}' angelegt.")
    return RedirectResponse("/admin/altersklassen", status_code=303)


@router.post("/altersklassen/{aid}/delete")
def altersklassen_delete(request: Request, aid: int, db: Session = Depends(get_db)):
    obj = db.get(Altersklasse, aid)
    safe_delete(request, db, obj, name=f"Altersklasse '{obj.Kuerzel}'" if obj else None)
    return RedirectResponse("/admin/altersklassen", status_code=303)


# ---------------- Geraete ----------------------------------------------------

@router.get("/geraete")
def geraete(request: Request, edit: Optional[int] = Query(None),
            db: Session = Depends(get_db)):
    items = db.query(Geraete).order_by(Geraete.Name).all()
    return render(request, db, "admin/geraete.html", items=items, edit_id=edit)


@router.post("/geraete/{gid}/update")
def geraete_update(request: Request, gid: int,
                   Name: str = Form(...), Einheit: str = Form("Pkt"),
                   Beschreibung: str = Form(""),
                   db: Session = Depends(get_db)):
    obj = db.get(Geraete, gid)
    if obj:
        obj.Name = Name.strip()
        obj.Einheit = Einheit.strip() or "Pkt"
        obj.Beschreibung = Beschreibung or None
        db.commit()
        flash(request, "success", f"Geraet '{obj.Name}' aktualisiert.")
    return RedirectResponse("/admin/geraete", status_code=303)


@router.post("/geraete")
def geraete_create(request: Request,
                   Name: str = Form(...), Einheit: str = Form("Pkt"),
                   Beschreibung: str = Form(""),
                   db: Session = Depends(get_db)):
    db.add(Geraete(Name=Name.strip(), Einheit=Einheit.strip() or "Pkt",
                   Beschreibung=Beschreibung or None))
    db.commit()
    flash(request, "success", f"Geraet '{Name}' angelegt.")
    return RedirectResponse("/admin/geraete", status_code=303)


@router.post("/geraete/{gid}/delete")
def geraete_delete(request: Request, gid: int, db: Session = Depends(get_db)):
    obj = db.get(Geraete, gid)
    safe_delete(request, db, obj, name=f"Geraet '{obj.Name}'" if obj else None)
    return RedirectResponse("/admin/geraete", status_code=303)


# ---------------- Berechnungs-Arten -----------------------------------------

@router.get("/berechnungen")
def berechnungen(request: Request, edit: Optional[int] = Query(None),
                 db: Session = Depends(get_db)):
    from scoring import REGISTRY
    items = db.query(BerechnungsArt).order_by(BerechnungsArt.Regel_Kuerzel).all()
    return render(request, db, "admin/berechnungen.html",
                  items=items, registry_codes=sorted(REGISTRY.keys()), edit_id=edit)


@router.post("/berechnungen/{bid}/update")
def berechnungen_update(request: Request, bid: int,
                        Regel_Kuerzel: str = Form(...),
                        Bezeichnung: str = Form(...),
                        Beschreibung: str = Form(""),
                        db: Session = Depends(get_db)):
    from scoring import REGISTRY
    obj = db.get(BerechnungsArt, bid)
    if obj:
        if Regel_Kuerzel not in REGISTRY:
            flash(request, "error",
                  f"'{Regel_Kuerzel}' kennt das Backend nicht.")
            return RedirectResponse("/admin/berechnungen", status_code=303)
        obj.Regel_Kuerzel = Regel_Kuerzel.strip()
        obj.Bezeichnung = Bezeichnung.strip()
        obj.Beschreibung = Beschreibung or None
        db.commit()
        flash(request, "success", f"Berechnung '{obj.Regel_Kuerzel}' aktualisiert.")
    return RedirectResponse("/admin/berechnungen", status_code=303)


@router.post("/berechnungen")
def berechnungen_create(request: Request,
                        Regel_Kuerzel: str = Form(...),
                        Bezeichnung: str = Form(...),
                        Beschreibung: str = Form(""),
                        db: Session = Depends(get_db)):
    from scoring import REGISTRY
    if Regel_Kuerzel not in REGISTRY:
        flash(request, "error",
              f"Kein Backend-Code fuer '{Regel_Kuerzel}'. "
              f"Verfuegbar: {', '.join(sorted(REGISTRY))}")
        return RedirectResponse("/admin/berechnungen", status_code=303)
    db.add(BerechnungsArt(Regel_Kuerzel=Regel_Kuerzel.strip(),
                          Bezeichnung=Bezeichnung.strip(),
                          Beschreibung=Beschreibung or None))
    db.commit()
    flash(request, "success", f"Berechnungs-Art '{Regel_Kuerzel}' angelegt.")
    return RedirectResponse("/admin/berechnungen", status_code=303)


@router.post("/berechnungen/{bid}/delete")
def berechnungen_delete(request: Request, bid: int, db: Session = Depends(get_db)):
    obj = db.get(BerechnungsArt, bid)
    safe_delete(request, db, obj,
                name=f"Berechnungs-Art '{obj.Regel_Kuerzel}'" if obj else None)
    return RedirectResponse("/admin/berechnungen", status_code=303)


# ---------------- Benutzer ---------------------------------------------------

@router.get("/users")
def users_list(request: Request, db: Session = Depends(get_db)):
    items = db.query(User).order_by(User.username).all()
    return render(request, db, "admin/users.html", items=items)


@router.post("/users")
def users_create(request: Request,
                 username: str = Form(...), email: str = Form(...),
                 password: str = Form(...), role: str = Form("viewer"),
                 db: Session = Depends(get_db)):
    if role not in ("admin", "tisch", "kampfrichter", "viewer"):
        flash(request, "error", "Ungueltige Rolle.")
        return RedirectResponse("/admin/users", status_code=303)
    db.add(User(username=username.strip(), email=email.strip(),
                password_hash=hash_password(password), role=role, is_active=1))
    db.commit()
    flash(request, "success", f"User '{username}' angelegt.")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{uid}/reset-password")
def users_reset_password(request: Request, uid: int,
                         new_password: str = Form(...),
                         db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if u:
        u.password_hash = hash_password(new_password)
        db.commit()
        flash(request, "success", f"Passwort von '{u.username}' zurueckgesetzt.")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{uid}/toggle-active")
def users_toggle_active(request: Request, uid: int,
                        current_admin=Depends(require_user("admin")),
                        db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u:
        return RedirectResponse("/admin/users", status_code=303)
    if u.id == current_admin.id:
        flash(request, "error", "Du kannst dich nicht selbst deaktivieren.")
        return RedirectResponse("/admin/users", status_code=303)
    u.is_active = 0 if u.is_active else 1
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{uid}/delete")
def users_delete(request: Request, uid: int,
                 current_admin=Depends(require_user("admin")),
                 db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u:
        return RedirectResponse("/admin/users", status_code=303)
    if u.id == current_admin.id:
        flash(request, "error", "Du kannst dich nicht selbst loeschen.")
        return RedirectResponse("/admin/users", status_code=303)
    db.delete(u)
    db.commit()
    flash(request, "success", "Benutzer geloescht.")
    return RedirectResponse("/admin/users", status_code=303)
