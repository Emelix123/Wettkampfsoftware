import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
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


# --- Massen-Import via CSV ---------------------------------------------------

CSV_COLUMNS = ["Vorname", "Nachname", "Geburtsdatum", "Verein_Kuerzel", "Geschlecht"]


def _parse_csv(raw: bytes) -> tuple[list[dict], list[str]]:
    """Parsen + sanftes Validieren. Returns (rows, errors).
    rows enthaelt fuer jede Zeile ein dict mit normalisierten Feldern."""
    errors: list[str] = []
    text = raw.decode("utf-8-sig", errors="replace")
    # Auto-detect Delimiter (Komma oder Semikolon)
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return [], ["CSV scheint leer zu sein."]
    fields = [f.strip() for f in reader.fieldnames]
    missing = [c for c in ("Vorname", "Nachname") if c not in fields]
    if missing:
        return [], [
            f"Pflicht-Spalten fehlen: {', '.join(missing)}. "
            f"Gefunden: {', '.join(fields)}. "
            f"Erwartet: {', '.join(CSV_COLUMNS)}."
        ]

    rows = []
    for i, raw_row in enumerate(reader, start=2):  # row 1 = Header
        row = {(k.strip() if k else ""): (v.strip() if v else "") for k, v in raw_row.items()}
        vor = row.get("Vorname", ""); nach = row.get("Nachname", "")
        if not vor or not nach:
            errors.append(f"Zeile {i}: Vorname oder Nachname fehlt — uebersprungen.")
            continue
        gd_raw = row.get("Geburtsdatum", "")
        gd = None
        if gd_raw:
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
                try:
                    from datetime import datetime
                    gd = datetime.strptime(gd_raw, fmt).date()
                    break
                except ValueError:
                    continue
            if gd is None:
                errors.append(f"Zeile {i}: Geburtsdatum '{gd_raw}' nicht erkannt — leer gelassen.")
        gs = (row.get("Geschlecht", "") or "").lower()
        if gs and gs not in ("m", "w", "d"):
            errors.append(f"Zeile {i}: Geschlecht '{gs}' ungueltig — leer gelassen.")
            gs = ""
        rows.append({
            "Vorname": vor, "Nachname": nach, "Geburtsdatum": gd,
            "Verein_Kuerzel": row.get("Verein_Kuerzel", ""),
            "Geschlecht": gs or None,
        })
    return rows, errors


@router.get("/import")
def import_form(request: Request, db: Session = Depends(get_db),
                user=Depends(require_user(("admin", "tisch")))):
    return render(request, db, "wettkampf/personen_import.html",
                  preview=None, errors=[], created_persons=0,
                  created_vereine=0, csv_columns=CSV_COLUMNS)


@router.post("/import")
async def import_upload(request: Request,
                        file: UploadFile = File(...),
                        modus: str = Form("preview"),
                        db: Session = Depends(get_db),
                        user=Depends(require_user(("admin", "tisch")))):
    raw = await file.read()
    rows, errors = _parse_csv(raw)
    if not rows and errors:
        return render(request, db, "wettkampf/personen_import.html",
                      preview=None, errors=errors, created_persons=0,
                      created_vereine=0, csv_columns=CSV_COLUMNS)

    if modus == "preview":
        # bestehende Vereine pruefen
        kuerzel_set = {r["Verein_Kuerzel"] for r in rows if r["Verein_Kuerzel"]}
        existing = {v.Kuerzel for v in db.query(Verein).filter(
            Verein.Kuerzel.in_(kuerzel_set or [""])
        ).all()}
        new_vereine = sorted(kuerzel_set - existing)
        return render(request, db, "wettkampf/personen_import.html",
                      preview=rows, errors=errors,
                      created_persons=0, created_vereine=0,
                      new_vereine=new_vereine, csv_columns=CSV_COLUMNS,
                      raw_csv=raw.decode("utf-8-sig", errors="replace"))

    # echter Import
    verein_cache = {v.Kuerzel: v for v in db.query(Verein).all()}
    created_p = 0; created_v = 0
    for r in rows:
        vk = r["Verein_Kuerzel"]
        verein_obj = None
        if vk:
            verein_obj = verein_cache.get(vk)
            if not verein_obj:
                verein_obj = Verein(Kuerzel=vk, Name=vk)
                db.add(verein_obj); db.commit(); db.refresh(verein_obj)
                verein_cache[vk] = verein_obj
                created_v += 1
        db.add(Personen(
            Vorname=r["Vorname"], Nachname=r["Nachname"],
            Geburtsdatum=r["Geburtsdatum"],
            Verein_id=verein_obj.idVerein if verein_obj else None,
            Geschlecht=r["Geschlecht"],
        ))
        created_p += 1
    db.commit()
    flash(request, "success", f"Import OK: {created_p} Personen, {created_v} neue Vereine.")
    return RedirectResponse("/personen", status_code=303)
