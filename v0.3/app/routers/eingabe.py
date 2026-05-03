"""Live-Eingabe der Versuche.

Modi:
  * "tisch"  (Default fuer admin/tisch): Eine Maske listet alle Athleten dieses
             Geraets; pro Athlet werden alle Richter-Wertungen in einer Zeile
             eingetragen.
  * "single" (Default fuer kampfrichter): Ein Athlet auf einmal, der eingeloggte
             User ist Richter Slot 1.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from live_pubsub import CHANNEL
from models import (
    Wettkampf, GeraeteHasWettkampf, PersonenHasWettkampf,
    EinzelErgebnis, KampfrichterWertung, KampfrichterWertungDetail,
)
from scoring import get_strategy
from services.score_service import recalc_versuch
from views import render, flash

router = APIRouter(prefix="/eingabe")


def _get_or_create_versuch(db: Session, wid: int, gid: int, pid: int, vnr: int) -> EinzelErgebnis:
    ee = (
        db.query(EinzelErgebnis)
        .filter_by(Wettkampf_id=wid, Geraete_id=gid,
                   Personen_id=pid, Versuch_Nr=vnr)
        .first()
    )
    if ee:
        return ee
    ee = EinzelErgebnis(
        Wettkampf_id=wid, Geraete_id=gid,
        Personen_id=pid, Versuch_Nr=vnr,
        Status="Offen", Ist_Gueltig=1,
    )
    db.add(ee); db.commit(); db.refresh(ee)
    return ee


@router.get("/{wid}")
def overview(request: Request, wid: int, db: Session = Depends(get_db),
             user=Depends(require_user(("admin", "tisch", "kampfrichter")))):
    wk = db.get(Wettkampf, wid)
    if not wk:
        flash(request, "error", "Wettkampf nicht gefunden.")
        return RedirectResponse("/tage", status_code=303)
    return render(request, db, "eingabe/overview.html", wk=wk)


@router.get("/{wid}/{gid}")
def geraet(request: Request, wid: int, gid: int,
           mode: Optional[str] = Query(None),
           riege: Optional[int] = Query(None),
           db: Session = Depends(get_db),
           user=Depends(require_user(("admin", "tisch", "kampfrichter")))):
    wk = db.get(Wettkampf, wid)
    ghw = (
        db.query(GeraeteHasWettkampf)
        .filter_by(Wettkampf_id=wid, Geraete_id=gid).first()
    )
    if not wk or not ghw:
        flash(request, "error", "Wettkampf oder Geraet nicht gefunden.")
        return RedirectResponse(f"/eingabe/{wid}", status_code=303)

    if not mode:
        mode = "tisch" if user.role in ("admin", "tisch") else "single"

    starter_q = (
        db.query(PersonenHasWettkampf)
        .filter_by(Wettkampf_id=wid)
        .filter(PersonenHasWettkampf.Start_Status.in_(["Gemeldet", "Gestartet"]))
    )
    if riege is not None:
        if riege == 0:  # 0 = ohne Riege
            starter_q = starter_q.filter(PersonenHasWettkampf.Riege_id.is_(None))
        else:
            starter_q = starter_q.filter(PersonenHasWettkampf.Riege_id == riege)
    starter = starter_q.order_by(PersonenHasWettkampf.Startnummer).all()

    versuche = (
        db.query(EinzelErgebnis)
        .filter_by(Wettkampf_id=wid, Geraete_id=gid)
        .all()
    )
    versuch_map: dict[tuple[int, int], EinzelErgebnis] = {
        (e.Personen_id, e.Versuch_Nr): e for e in versuche
    }
    # Wertungen pro Versuch: dict[(pid, vnr)] -> dict[slot] -> dict[Krit, Wert]
    wertung_map: dict[tuple[int, int], dict[int, dict[str, float]]] = {}
    for e in versuche:
        slots: dict[int, dict[str, float]] = {}
        for w in e.wertungen:
            slots[w.Richter_Slot] = {d.Kriterium: float(d.Wert) for d in w.details}
        wertung_map[(e.Personen_id, e.Versuch_Nr)] = slots

    strategy = get_strategy(ghw.berechnung.Regel_Kuerzel)
    return render(request, db, "eingabe/geraet.html",
                  wk=wk, ghw=ghw, mode=mode, starter=starter,
                  versuch_map=versuch_map, wertung_map=wertung_map,
                  kriterien=strategy.required_kriterien,
                  num_judges=ghw.Erwartete_Kampfrichter,
                  versuche_max=ghw.Anzahl_Versuche,
                  riege_filter=riege)


@router.post("/{wid}/{gid}/save")
async def save(request: Request, wid: int, gid: int,
               db: Session = Depends(get_db),
               user=Depends(require_user(("admin", "tisch", "kampfrichter")))):
    """Form-Felder:
        pid          - Personen_id
        versuch      - Versuch_Nr
        ist_gueltig  - "1" / "0"
        slotN__<Krit> - Wert (z.B. slot1__D_Note=4.2)
    Im Single-Mode (kampfrichter) erzwingt das Backend Slot=1.
    """
    wk = db.get(Wettkampf, wid)
    ghw = (
        db.query(GeraeteHasWettkampf)
        .filter_by(Wettkampf_id=wid, Geraete_id=gid).first()
    )
    if not wk or not ghw:
        return RedirectResponse(f"/eingabe/{wid}", status_code=303)

    form = dict(await request.form())
    try:
        pid = int(form.get("pid", "0"))
        versuch = int(form.get("versuch", "1"))
    except ValueError:
        flash(request, "error", "Ungueltige Form-Daten.")
        return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)

    # Checkbox: HTML schickt das Feld nur wenn angekreuzt -> Anwesenheit pruefen.
    ist_gueltig = "ist_gueltig" in form

    # Optimistic Locking: hat sich der Versuch geaendert seit das Form geladen wurde?
    seen_updated_at = form.get("updated_at", "").strip()
    existing_ee = (
        db.query(EinzelErgebnis)
        .filter_by(Wettkampf_id=wid, Geraete_id=gid,
                   Personen_id=pid, Versuch_Nr=versuch).first()
    )
    if existing_ee and seen_updated_at and existing_ee.Updated_At:
        current_iso = existing_ee.Updated_At.isoformat(timespec="seconds")
        if current_iso != seen_updated_at:
            flash(request, "error",
                  f"Versuch wurde inzwischen von jemand anderem geaendert "
                  f"(jetzt: {current_iso}, dein Stand: {seen_updated_at}). "
                  f"Bitte Seite neu laden, dann nochmal speichern.")
            return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)

    ee = _get_or_create_versuch(db, wid, gid, pid, versuch)
    ee.Ist_Gueltig = 1 if ist_gueltig else 0
    ee.Status = "In_Bewertung"
    ee.Erfasst_Von = user.id
    db.commit()

    slot_data: dict[int, dict[str, float]] = {}
    bad_inputs: list[str] = []
    for key, value in form.items():
        if "__" not in key or not key.startswith("slot"):
            continue
        slot_str, krit = key.split("__", 1)
        try:
            slot = int(slot_str.replace("slot", ""))
        except ValueError:
            continue
        s_value = str(value).strip().replace(",", ".")
        if s_value == "":
            continue
        try:
            wert = float(s_value)
        except ValueError:
            bad_inputs.append(f"R{slot}/{krit}='{s_value}'")
            continue
        slot_data.setdefault(slot, {})[krit] = wert
    if bad_inputs:
        flash(request, "error",
              "Ungueltige Werte (nicht numerisch) wurden ignoriert: "
              + ", ".join(bad_inputs))

    # Single-Mode (kampfrichter): nur die EIGENE Wertung speichern.
    # Slot-Logik:
    #   - hat dieser User schon eine Wertung fuer diesen Versuch? -> denselben Slot ueberschreiben
    #   - sonst: naechsten freien Slot vergeben (1..N), kollidiert nicht mit anderen Richtern
    if user.role == "kampfrichter":
        eingabe_slot_keys = list(slot_data.keys())
        if not eingabe_slot_keys:
            return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)
        # Ignoriere alle Slots ausser dem ersten (Single-Mode-Form hat eh nur slot1)
        eingabe_kv = slot_data[eingabe_slot_keys[0]]

        own = (
            db.query(KampfrichterWertung)
            .filter_by(Einzel_Ergebnis_id=ee.idEinzel_Ergebnis, Richter_user_id=user.id)
            .first()
        )
        if own:
            target_slot = own.Richter_Slot
        else:
            used = {
                w.Richter_Slot for w in
                db.query(KampfrichterWertung)
                .filter_by(Einzel_Ergebnis_id=ee.idEinzel_Ergebnis).all()
            }
            target_slot = next(s for s in range(1, 100) if s not in used)
        slot_data = {target_slot: eingabe_kv}

    for slot, kv in slot_data.items():
        if not kv:
            continue
        existing = (
            db.query(KampfrichterWertung)
            .filter_by(Einzel_Ergebnis_id=ee.idEinzel_Ergebnis, Richter_Slot=slot)
            .first()
        )
        if existing:
            db.delete(existing); db.commit()
        w = KampfrichterWertung(
            Einzel_Ergebnis_id=ee.idEinzel_Ergebnis,
            Richter_user_id=user.id if user.role == "kampfrichter" else None,
            Richter_Slot=slot,
            Erfasst_Von=user.id,
        )
        db.add(w); db.commit(); db.refresh(w)
        for krit, wert in kv.items():
            db.add(KampfrichterWertungDetail(
                Wertung_id=w.idWertung, Kriterium=krit, Wert=wert,
            ))
        db.commit()

    recalc_versuch(db, ee)
    # Audit-Log
    from services import audit
    audit.log(db, user, "ergebnis.save",
              "EinzelErgebnis", ee.idEinzel_Ergebnis,
              {"wettkampf_id": wid, "geraet_id": gid, "person_id": pid,
               "versuch": versuch, "score": float(ee.Score) if ee.Score is not None else None,
               "ist_gueltig": bool(ee.Ist_Gueltig)})
    # Live-Subscriber benachrichtigen — Rangliste in allen offenen Tabs
    # aktualisiert sich sofort via WebSocket-Trigger.
    await CHANNEL.publish(wid)
    flash(request, "success", f"Versuch {versuch} fuer Startnummer/Person #{pid} gespeichert.")
    return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)


@router.post("/{wid}/{gid}/slot/delete")
async def slot_delete(request: Request, wid: int, gid: int,
                      db: Session = Depends(get_db),
                      user=Depends(require_user(("admin", "tisch", "kampfrichter")))):
    """Loescht eine einzelne Richter-Wertung (1 Slot) und rechnet neu durch.
    Im Kampfrichter-Mode darf nur die EIGENE Wertung geloescht werden."""
    form = dict(await request.form())
    pid = int(form.get("pid", "0"))
    versuch = int(form.get("versuch", "1"))
    slot = int(form.get("slot", "0"))
    ee = (
        db.query(EinzelErgebnis)
        .filter_by(Wettkampf_id=wid, Geraete_id=gid,
                   Personen_id=pid, Versuch_Nr=versuch).first()
    )
    if not ee:
        return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)
    w = (
        db.query(KampfrichterWertung)
        .filter_by(Einzel_Ergebnis_id=ee.idEinzel_Ergebnis, Richter_Slot=slot)
        .first()
    )
    if not w:
        return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)
    if user.role == "kampfrichter" and w.Richter_user_id != user.id:
        flash(request, "error", "Du kannst nur deine eigene Wertung loeschen.")
        return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)
    # ID merken — nach delete+commit ist das Python-Objekt expired.
    wertung_id = w.idWertung
    db.delete(w); db.commit()
    recalc_versuch(db, ee)
    from services import audit
    audit.log(db, user, "wertung.slot_delete",
              "KampfrichterWertung", wertung_id,
              {"wettkampf_id": wid, "geraet_id": gid,
               "person_id": pid, "versuch": versuch, "slot": slot})
    await CHANNEL.publish(wid)
    flash(request, "success", f"Slot R{slot} geloescht und neu berechnet.")
    return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)


@router.post("/{wid}/{gid}/clear")
async def clear_versuch(request: Request, wid: int, gid: int,
                        db: Session = Depends(get_db),
                        user=Depends(require_user(("admin", "tisch")))):
    form = dict(await request.form())
    pid = int(form.get("pid", "0")); versuch = int(form.get("versuch", "1"))
    ee = (
        db.query(EinzelErgebnis)
        .filter_by(Wettkampf_id=wid, Geraete_id=gid,
                   Personen_id=pid, Versuch_Nr=versuch).first()
    )
    if ee:
        from services import audit
        audit.log(db, user, "ergebnis.clear",
                  "EinzelErgebnis", ee.idEinzel_Ergebnis,
                  {"wettkampf_id": wid, "geraet_id": gid,
                   "person_id": pid, "versuch": versuch})
        db.delete(ee); db.commit()
        await CHANNEL.publish(wid)
        flash(request, "success", "Versuch geloescht.")
    return RedirectResponse(f"/eingabe/{wid}/{gid}", status_code=303)
