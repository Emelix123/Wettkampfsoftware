"""Oeffentliche Live-Ansicht (kein Login noetig)."""
import asyncio

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from live_pubsub import CHANNEL
from models import Wettkampf, WettkampfTag
from services.rangliste import (
    einzel_rangliste_mit_geraeten, mannschaft_rangliste, riegen_fortschritt,
)
from views import render

router = APIRouter(prefix="/live")


@router.get("")
def live_index(request: Request, db: Session = Depends(get_db)):
    tage = (
        db.query(WettkampfTag)
        .order_by(WettkampfTag.Wettkampf_Datum.desc())
        .limit(20).all()
    )
    return render(request, db, "live/index.html", tage=tage)


@router.get("/tag/{tid}")
def tag(request: Request, tid: int, db: Session = Depends(get_db)):
    tag = db.get(WettkampfTag, tid)
    if not tag:
        return RedirectResponse("/live", status_code=303)
    return render(request, db, "live/tag.html", tag=tag)


@router.get("/wettkampf/{wid}")
def wettkampf(request: Request, wid: int, db: Session = Depends(get_db)):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/live", status_code=303)
    return render(request, db, "live/wettkampf.html", wk=wk)


# HTMX-Partial: nur die Rangliste, getriggert per WebSocket bzw. 30s-Backup-Poll
@router.get("/wettkampf/{wid}/rangliste")
def wettkampf_rangliste(request: Request, wid: int, db: Session = Depends(get_db)):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/live", status_code=303)
    einzel, geraete = einzel_rangliste_mit_geraeten(db, wid)
    teams = []
    if wk.Typ != "Einzel":
        teams = mannschaft_rangliste(db, wid, wk.Mannschaft_Groesse)
    return render(request, db, "live/_rangliste.html",
                  wk=wk, einzel=einzel, teams=teams, geraete=geraete)


# WebSocket fuer Live-Push. Nachricht ist nur ein Trigger ("update"),
# der eigentliche Inhalt wird via HTMX-GET nachgeladen.
@router.websocket("/wettkampf/{wid}/ws")
async def wettkampf_ws(ws: WebSocket, wid: int):
    await ws.accept()
    q = await CHANNEL.subscribe(wid)
    try:
        # Beim Connect direkt einen Update-Tick schicken, damit der Client
        # initial die Daten zieht (wir haben hx-trigger="load" aber auch
        # "ws message" — doppelt schadet nicht).
        await ws.send_text("update")
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=30.0)
                await ws.send_text(msg)
            except asyncio.TimeoutError:
                # Heartbeat damit Proxies die Verbindung nicht killen
                await ws.send_text("ping")
    except WebSocketDisconnect:
        pass
    finally:
        await CHANNEL.unsubscribe(wid, q)


# Live: Detail-Aufschluesselung pro Athlet (alle Versuche + Wertungen)
@router.get("/wettkampf/{wid}/athlet/{pid}")
def athlet_detail(request: Request, wid: int, pid: int,
                  db: Session = Depends(get_db)):
    from models import Personen, EinzelErgebnis
    wk = db.get(Wettkampf, wid)
    person = db.get(Personen, pid)
    if not wk or not person:
        return RedirectResponse("/live", status_code=303)
    versuche = (
        db.query(EinzelErgebnis)
        .filter_by(Wettkampf_id=wid, Personen_id=pid)
        .order_by(EinzelErgebnis.Geraete_id, EinzelErgebnis.Versuch_Nr)
        .all()
    )
    # Per Geraet gruppieren
    from collections import defaultdict
    by_geraet: dict[int, list] = defaultdict(list)
    for ee in versuche:
        by_geraet[ee.Geraete_id].append(ee)
    return render(request, db, "live/athlet_detail.html",
                  wk=wk, person=person, by_geraet=by_geraet)


# Live: Riege-Uebersicht — wo ist welche Riege gerade
@router.get("/tag/{tid}/riegen")
def tag_riegen(request: Request, tid: int, db: Session = Depends(get_db)):
    tag = db.get(WettkampfTag, tid)
    if not tag:
        return RedirectResponse("/live", status_code=303)
    fortschritt_per_wk = {
        w.idWettkampf: riegen_fortschritt(db, w.idWettkampf)
        for w in tag.wettkaempfe
    }
    return render(request, db, "live/tag_riegen.html",
                  tag=tag, fortschritt_per_wk=fortschritt_per_wk)


# Profil-Seite eines Athleten (alle Wettkaempfe)
@router.get("/athlet/{pid}")
def athlet_profil(request: Request, pid: int, db: Session = Depends(get_db)):
    from models import Personen, PersonenHasWettkampf
    person = db.get(Personen, pid)
    if not person:
        return RedirectResponse("/live", status_code=303)
    teilnahmen = (
        db.query(PersonenHasWettkampf)
        .filter_by(Personen_id=pid)
        .all()
    )
    # Per teilnahme den GesamtScore aus der View holen
    from sqlalchemy import text
    stats = {}
    if teilnahmen:
        rows = db.execute(text("""
            SELECT g.Wettkampf_id, g.GesamtScore, r.Platz
            FROM vw_Gesamt_Ergebnisse g
            LEFT JOIN vw_Rangliste_Einzel r
                   ON r.Wettkampf_id = g.Wettkampf_id
                  AND r.Personen_id  = g.Personen_id
            WHERE g.Personen_id = :pid
        """), {"pid": pid}).mappings().all()
        stats = {r["Wettkampf_id"]: dict(r) for r in rows}
    return render(request, db, "live/athlet_profil.html",
                  person=person, teilnahmen=teilnahmen, stats=stats)
