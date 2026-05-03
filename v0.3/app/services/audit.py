"""Audit-Logging — wer hat wann was gemacht.

Aufruf-Beispiel:
    audit.log(db, user, 'ergebnis.save', 'EinzelErgebnis', ee.idEinzel_Ergebnis,
              {'score': float(ee.Score), 'wettkampf_id': ee.Wettkampf_id})
"""
from typing import Optional

from sqlalchemy.orm import Session

from models import AuditLog, User


def log(
    db: Session,
    user: Optional[User],
    aktion: str,
    ziel_typ: Optional[str] = None,
    ziel_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    try:
        entry = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            aktion=aktion,
            ziel_typ=ziel_typ,
            ziel_id=str(ziel_id) if ziel_id is not None else None,
            details=details,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        # Audit-Log-Fehler sollen NIE die eigentliche Operation killen
        print(f"[audit] log failed: {e}")
        db.rollback()
