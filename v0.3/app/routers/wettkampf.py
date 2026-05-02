from datetime import time
from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request  # noqa
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models import (
    Wettkampf, WettkampfTag, Geraete, BerechnungsArt, GeraeteHasWettkampf,
    Riege, Mannschaft, Verein, PersonenHasWettkampf,
)
from views import render, flash, safe_delete

router = APIRouter()


# --- Wettkampf -------------------------------------------------------------

@router.post("/wettkampf")
def create_wettkampf(request: Request, tag_id: int = Query(...),
                     Wettkampf_Nr: int = Form(...), Name: str = Form(...),
                     Altersklasse_id: int = Form(...), Typ: str = Form("Einzel"),
                     Mannschaft_Groesse: str = Form(""),
                     db: Session = Depends(get_db),
                     user=Depends(require_user("admin"))):
    if not db.get(WettkampfTag, tag_id):
        flash(request, "error", "Wettkampftag existiert nicht.")
        return RedirectResponse("/tage", status_code=303)
    db.add(Wettkampf(
        Wettkampf_Tag_id=tag_id, Wettkampf_Nr=Wettkampf_Nr, Name=Name.strip(),
        Altersklasse_id=Altersklasse_id, Typ=Typ,
        Mannschaft_Groesse=int(Mannschaft_Groesse) if Mannschaft_Groesse else None,
    ))
    db.commit()
    flash(request, "success", f"Wettkampf '{Name}' angelegt.")
    return RedirectResponse(f"/tage/{tag_id}", status_code=303)


@router.get("/wettkampf/{wid}")
def show_wettkampf(request: Request, wid: int,
                   edit_ghw: Optional[int] = Query(None),
                   db: Session = Depends(get_db),
                   user=Depends(require_user())):
    from models import Altersklasse
    wk = db.get(Wettkampf, wid)
    if not wk:
        flash(request, "error", "Wettkampf nicht gefunden.")
        return RedirectResponse("/tage", status_code=303)
    geraete_alle = db.query(Geraete).order_by(Geraete.Name).all()
    berechnungen = db.query(BerechnungsArt).order_by(BerechnungsArt.Bezeichnung).all()
    vereine = db.query(Verein).order_by(Verein.Kuerzel).all()
    altersklassen = db.query(Altersklasse).order_by(Altersklasse.Kuerzel).all()

    anmeldungen = (
        db.query(PersonenHasWettkampf)
        .filter_by(Wettkampf_id=wid)
        .order_by(PersonenHasWettkampf.Startnummer)
        .all()
    )
    return render(request, db, "wettkampf/wettkampf_detail.html",
                  wk=wk, geraete_alle=geraete_alle, berechnungen=berechnungen,
                  vereine=vereine, anmeldungen=anmeldungen,
                  altersklassen=altersklassen, edit_ghw=edit_ghw)


@router.post("/wettkampf/{wid}/status")
def set_status(request: Request, wid: int, Status: str = Form(...),
               db: Session = Depends(get_db),
               user=Depends(require_user("admin"))):
    wk = db.get(Wettkampf, wid)
    if wk:
        wk.Status = Status
        db.commit()
        flash(request, "success", f"Status gesetzt auf '{Status}'.")
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


@router.post("/wettkampf/{wid}/update")
def update_wettkampf(request: Request, wid: int,
                     Wettkampf_Nr: int = Form(...),
                     Name: str = Form(...),
                     Altersklasse_id: int = Form(...),
                     Typ: str = Form("Einzel"),
                     Mannschaft_Groesse: str = Form(""),
                     db: Session = Depends(get_db),
                     user=Depends(require_user("admin"))):
    wk = db.get(Wettkampf, wid)
    if wk:
        wk.Wettkampf_Nr = Wettkampf_Nr
        wk.Name = Name.strip()
        wk.Altersklasse_id = Altersklasse_id
        wk.Typ = Typ
        wk.Mannschaft_Groesse = int(Mannschaft_Groesse) if Mannschaft_Groesse else None
        db.commit()
        flash(request, "success", "Wettkampf aktualisiert.")
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


@router.post("/wettkampf/{wid}/delete")
def delete_wettkampf(request: Request, wid: int, db: Session = Depends(get_db),
                     user=Depends(require_user("admin"))):
    wk = db.get(Wettkampf, wid)
    tid = wk.Wettkampf_Tag_id if wk else None
    safe_delete(request, db, wk, name=f"Wettkampf '{wk.Name}'" if wk else None)
    return RedirectResponse(f"/tage/{tid}" if tid else "/tage", status_code=303)


# --- Geraete-Zuordnung ------------------------------------------------------

@router.post("/wettkampf/{wid}/geraete")
def add_geraet(request: Request, wid: int,
               Geraete_id: int = Form(...), Berechnungs_Art_id: int = Form(...),
               Anzahl_Versuche: int = Form(1),
               Erwartete_Kampfrichter: int = Form(1),
               Score_Faktor: float = Form(1.0), Score_Offset: float = Form(0.0),
               db: Session = Depends(get_db),
               user=Depends(require_user("admin"))):
    next_order = (
        db.query(GeraeteHasWettkampf).filter_by(Wettkampf_id=wid).count() + 1
    )
    db.add(GeraeteHasWettkampf(
        Wettkampf_id=wid, Geraete_id=Geraete_id,
        Berechnungs_Art_id=Berechnungs_Art_id,
        Anzahl_Versuche=Anzahl_Versuche,
        Erwartete_Kampfrichter=Erwartete_Kampfrichter,
        Score_Faktor=Score_Faktor, Score_Offset=Score_Offset,
        Reihenfolge=next_order,
    ))
    db.commit()
    flash(request, "success", "Geraet zugeordnet.")
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


@router.post("/wettkampf/{wid}/geraete/{ghw}/update")
def update_geraet(request: Request, wid: int, ghw: int,
                  Berechnungs_Art_id: int = Form(...),
                  Anzahl_Versuche: int = Form(1),
                  Erwartete_Kampfrichter: int = Form(1),
                  Score_Faktor: float = Form(1.0),
                  Score_Offset: float = Form(0.0),
                  db: Session = Depends(get_db),
                  user=Depends(require_user("admin"))):
    obj = db.get(GeraeteHasWettkampf, ghw)
    if obj and obj.Wettkampf_id == wid:
        obj.Berechnungs_Art_id = Berechnungs_Art_id
        obj.Anzahl_Versuche = Anzahl_Versuche
        obj.Erwartete_Kampfrichter = Erwartete_Kampfrichter
        obj.Score_Faktor = Score_Faktor
        obj.Score_Offset = Score_Offset
        db.commit()
        flash(request, "success", f"Geraet '{obj.geraet.Name}' aktualisiert.")
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


@router.post("/wettkampf/{wid}/geraete/{ghw}/move")
def move_geraet(request: Request, wid: int, ghw: int,
                direction: str = Form(...),
                db: Session = Depends(get_db),
                user=Depends(require_user("admin"))):
    """direction = 'up' oder 'down' — tauscht Reihenfolge mit Nachbar."""
    obj = db.get(GeraeteHasWettkampf, ghw)
    if not obj or obj.Wettkampf_id != wid:
        return RedirectResponse(f"/wettkampf/{wid}", status_code=303)
    others = (
        db.query(GeraeteHasWettkampf)
        .filter_by(Wettkampf_id=wid)
        .order_by(GeraeteHasWettkampf.Reihenfolge)
        .all()
    )
    # Reihenfolge normalisieren falls Lücken
    for i, g in enumerate(others, 1):
        g.Reihenfolge = i
    db.commit()
    idx = next(i for i, g in enumerate(others) if g.idGhW == ghw)
    if direction == "up" and idx > 0:
        others[idx].Reihenfolge, others[idx-1].Reihenfolge = (
            others[idx-1].Reihenfolge, others[idx].Reihenfolge,
        )
    elif direction == "down" and idx < len(others) - 1:
        others[idx].Reihenfolge, others[idx+1].Reihenfolge = (
            others[idx+1].Reihenfolge, others[idx].Reihenfolge,
        )
    db.commit()
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


@router.post("/wettkampf/{wid}/geraete/{ghw}/delete")
def del_geraet(request: Request, wid: int, ghw: int,
               db: Session = Depends(get_db),
               user=Depends(require_user("admin"))):
    obj = db.get(GeraeteHasWettkampf, ghw)
    if obj and obj.Wettkampf_id == wid:
        safe_delete(request, db, obj, name=f"Geraet '{obj.geraet.Name}'")
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


# --- Riegen -----------------------------------------------------------------

@router.post("/wettkampf/{wid}/riegen")
def add_riege(request: Request, wid: int,
              Bezeichnung: str = Form(...), Start_Zeit: str = Form(""),
              db: Session = Depends(get_db),
              user=Depends(require_user("admin"))):
    db.add(Riege(Wettkampf_id=wid, Bezeichnung=Bezeichnung.strip(),
                 Start_Zeit=time.fromisoformat(Start_Zeit) if Start_Zeit else None))
    db.commit()
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


@router.post("/wettkampf/{wid}/riegen/{rid}/delete")
def del_riege(request: Request, wid: int, rid: int,
              db: Session = Depends(get_db),
              user=Depends(require_user("admin"))):
    obj = db.get(Riege, rid)
    if obj and obj.Wettkampf_id == wid:
        db.delete(obj); db.commit()
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


# --- Mannschaften -----------------------------------------------------------

@router.post("/wettkampf/{wid}/mannschaften")
def add_mannschaft(request: Request, wid: int,
                   Name: str = Form(...), Verein_id: str = Form(""),
                   db: Session = Depends(get_db),
                   user=Depends(require_user("admin"))):
    db.add(Mannschaft(Wettkampf_id=wid, Name=Name.strip(),
                      Verein_id=int(Verein_id) if Verein_id else None))
    db.commit()
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)


@router.post("/wettkampf/{wid}/mannschaften/{mid}/delete")
def del_mannschaft(request: Request, wid: int, mid: int,
                   db: Session = Depends(get_db),
                   user=Depends(require_user("admin"))):
    obj = db.get(Mannschaft, mid)
    if obj and obj.Wettkampf_id == wid:
        db.delete(obj); db.commit()
    return RedirectResponse(f"/wettkampf/{wid}", status_code=303)
