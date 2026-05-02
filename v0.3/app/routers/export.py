"""PDF-Exporte mit WeasyPrint.

Routen:
  /export/wettkampf/{wid}/startliste.pdf
  /export/wettkampf/{wid}/ergebnisse.pdf
  /export/wettkampf/{wid}/urkunden.pdf
  /export/tag/{tid}/ergebnisse.pdf
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.orm import Session
from weasyprint import HTML

from auth import require_user
from database import get_db
from models import Wettkampf, WettkampfTag, PersonenHasWettkampf
from services.rangliste import einzel_rangliste, mannschaft_rangliste
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
def ergebnisse(wid: int, db: Session = Depends(get_db),
               user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    einzel = einzel_rangliste(db, wid)
    teams = mannschaft_rangliste(db, wid, wk.Mannschaft_Groesse) if wk.Typ != "Einzel" else []
    pdf = _render_pdf("pdf/ergebnisse.html", wk=wk, einzel=einzel, teams=teams)
    return _pdf_response(pdf, f"ergebnisse-wk{wid}.pdf")


@router.get("/wettkampf/{wid}/urkunden.pdf")
def urkunden(wid: int, db: Session = Depends(get_db),
             user=Depends(require_user())):
    wk = db.get(Wettkampf, wid)
    if not wk:
        return RedirectResponse("/tage", status_code=303)
    einzel = einzel_rangliste(db, wid)
    pdf = _render_pdf("pdf/urkunden.html", wk=wk, einzel=einzel)
    return _pdf_response(pdf, f"urkunden-wk{wid}.pdf")


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
