"""Public Media-Endpoints fuer Logos (kein Login noetig).

URLs:
  /media/verein/{vid}/logo
  /media/wettkampftag/{tid}/logo
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Verein, WettkampfTag

router = APIRouter(prefix="/media")


def _serve(blob: bytes | None, mime: str | None) -> Response:
    if not blob:
        return Response(status_code=404)
    return Response(content=blob, media_type=mime or "image/png",
                    headers={"Cache-Control": "public, max-age=300"})


@router.get("/verein/{vid}/logo")
def verein_logo(vid: int, db: Session = Depends(get_db)):
    obj = db.get(Verein, vid)
    return _serve(obj.Logo if obj else None, obj.Logo_MimeType if obj else None)


@router.get("/wettkampftag/{tid}/logo")
def tag_logo(tid: int, db: Session = Depends(get_db)):
    obj = db.get(WettkampfTag, tid)
    return _serve(obj.Logo if obj else None, obj.Logo_MimeType if obj else None)
