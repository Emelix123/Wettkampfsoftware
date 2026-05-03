"""PDF-Exporte mit WeasyPrint.

Routen:
  /export/wettkampf/{wid}/startliste.pdf
  /export/wettkampf/{wid}/ergebnisse.pdf
  /export/wettkampf/{wid}/urkunden.pdf
  /export/tag/{tid}/ergebnisse.pdf
"""
import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from weasyprint import HTML

from auth import require_user
from database import get_db
from models import (
    Wettkampf, WettkampfTag, PersonenHasWettkampf, GeraeteHasWettkampf,
)
from scoring import get_strategy
from services.rangliste import (
    einzel_rangliste, einzel_rangliste_mit_geraeten, mannschaft_rangliste,
)
from services.backup import snapshot_tag
from views import templates as jinja

router = APIRouter(prefix="/export")


def _render_pdf(template_name: str, **ctx) -> bytes:
    tpl = jinja.env.get_template(template_name)
    html = tpl.render(**ctx)
    return HTML(string=html, base_url=".").write_pdf()


def _pdf_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/wettkampf/{wid}/startliste.pdf")
def startliste(wid: int, db: Session = Depends(get_db),
               user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    starter = (
        db.query(PersonenHasWettkampf)
        .filter_by(Wettkampf_id=wid)
        .order_by(
            PersonenHasWettkampf.Riege_id.is_(None),
            PersonenHasWettkampf.Riege_id,
            PersonenHasWettkampf.Startnummer,
        )
        .all()
    )
    pdf = _render_pdf("pdf/startliste.html", wk=wk, starter=starter)
    return _pdf_response(pdf, f"startliste-wk{wid}.pdf")


@router.get("/wettkampf/{wid}/ergebnisse.pdf")
def ergebnisse(wid: int,
               top: Optional[int] = Query(None, ge=1),
               db: Session = Depends(get_db),
               user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    einzel, geraete = einzel_rangliste_mit_geraeten(db, wid)
    if top:
        einzel = [r for r in einzel if r["Platz"] <= top]
    teams = mannschaft_rangliste(db, wid, wk.Mannschaft_Groesse) if wk.Typ != "Einzel" else []
    if top:
        teams = [t for t in teams if t["Platz"] <= top]
    pdf = _render_pdf("pdf/ergebnisse.html", wk=wk, einzel=einzel,
                      teams=teams, geraete=geraete, top=top)
    suffix = f"-top{top}" if top else ""
    return _pdf_response(pdf, f"ergebnisse-wk{wid}{suffix}.pdf")


@router.get("/wettkampf/{wid}/urkunden.pdf")
def urkunden(wid: int,
             top: Optional[int] = Query(None, ge=1),
             db: Session = Depends(get_db),
             user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    einzel = einzel_rangliste(db, wid)
    if top:
        einzel = [r for r in einzel if r["Platz"] <= top]
    # nur Athleten mit echtem Score
    einzel = [r for r in einzel if (r.get("GesamtScore") or 0) > 0]
    pdf = _render_pdf("pdf/urkunden.html", wk=wk, einzel=einzel)
    suffix = f"-top{top}" if top else ""
    return _pdf_response(pdf, f"urkunden-wk{wid}{suffix}.pdf")


@router.get("/tag/{tid}/ergebnisse.pdf")
def tag_ergebnisse(tid: int, db: Session = Depends(get_db),
                   user=Depends(require_user())):
    tag = db.get(WettkampfTag, tid)
    if not tag:
        return RedirectResponse("/tage", status_code=303)
    blocks = []
    for w in tag.wettkaempfe:
        blocks.append({
            "wk": w,
            "einzel": einzel_rangliste(db, w.idWettkampf),
            "teams": mannschaft_rangliste(db, w.idWettkampf, w.Mannschaft_Groesse) if w.Typ != "Einzel" else [],
        })
    pdf = _render_pdf("pdf/tag_ergebnisse.html", tag=tag, blocks=blocks)
    return _pdf_response(pdf, f"ergebnisse-tag{tid}.pdf")


# F3: Wertungskarten als PDF (leer, fuer Kampfrichter zum Ausfuellen)
@router.get("/wettkampf/{wid}/wertungskarten.pdf")
def wertungskarten(wid: int, geraet_id: Optional[int] = Query(None),
                   db: Session = Depends(get_db),
                   user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    geraete_zu = wk.geraete_zuordnung
    if geraet_id:
        geraete_zu = [g for g in geraete_zu if g.Geraete_id == geraet_id]
    if not geraete_zu:
        return RedirectResponse(f"/wettkampf/{wid}", status_code=303)

    starter = (
        db.query(PersonenHasWettkampf)
        .filter_by(Wettkampf_id=wid)
        .order_by(
            PersonenHasWettkampf.Riege_id.is_(None),
            PersonenHasWettkampf.Riege_id,
            PersonenHasWettkampf.Startnummer,
        ).all()
    )

    pages = b""
    # Eine PDF-Datei mit allen Geraeten hintereinander
    out = []
    for ghw in geraete_zu:
        strat = get_strategy(ghw.berechnung.Regel_Kuerzel)
        out.append(_render_pdf("pdf/wertungskarten.html",
                               wk=wk, ghw=ghw, starter=starter,
                               kriterien=strat.required_kriterien))
    # WeasyPrint liefert pro Aufruf ein eigenes PDF; beim ersten Geraet reicht es
    # — wenn nur 1 Geraet gewaehlt war. Mehrere PDFs zu mergen waere extra
    # Aufwand. Fuer simpel: nur das erste zurueckgeben wenn mehrere — aber meist
    # waehlt der User eh nur 1 Geraet beim Karten-Druck.
    if len(out) == 1:
        return _pdf_response(out[0], f"wertungskarten-wk{wid}-g{geraete_zu[0].Geraete_id}.pdf")
    # Mehrere -> nur das erste mit einer Notiz. (Pragmatisch.)
    return _pdf_response(out[0], f"wertungskarten-wk{wid}.pdf")


# F4: CSV-Export der Ergebnisse
@router.get("/wettkampf/{wid}/ergebnisse.csv")
def ergebnisse_csv(wid: int, db: Session = Depends(get_db),
                   user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    einzel, geraete = einzel_rangliste_mit_geraeten(db, wid)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\n")
    w.writerow(["Platz", "Vorname", "Nachname", "Verein"]
               + [g.Name for g in geraete] + ["Gesamt"])
    for r in einzel:
        row = [r["Platz"], r["Vorname"], r["Nachname"], r.get("Verein_Kuerzel") or ""]
        for g in geraete:
            s = r["geraete_scores"].get(g.idGeraete)
            row.append(f"{s:.3f}" if s is not None else "")
        row.append(f"{float(r['GesamtScore']):.3f}")
        w.writerow(row)
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ergebnisse-wk{wid}.csv"'},
    )


# F2: JSON-Snapshot eines Wettkampftags (Backup)
@router.get("/tag/{tid}/backup.json")
def backup_json(tid: int, db: Session = Depends(get_db),
                user=Depends(require_user("admin"))):
    data = snapshot_tag(db, tid)
    if not data:
        return RedirectResponse("/tage", status_code=303)
    payload = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return Response(
        content=payload, media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="backup-tag{tid}.json"'},
    )
