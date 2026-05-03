"""Einfaches In-Memory Rate-Limit fuer Login-Versuche.

Ohne Redis o.ae.: Dict[str -> list[float]]. Pro Worker getrennt
(bei 1 uvicorn-Worker — Default — egal). Bei Multi-Worker waere
ein Shared-Store noetig.

Limit: 5 fehlgeschlagene Logins pro Schluessel in 5 Minuten.
Nach Ueberschreitung: bis 5 Min ab dem letzten Versuch gesperrt.
"""
import time
from collections import defaultdict
from threading import Lock

WINDOW_SEC = 300        # 5 Minuten
MAX_FAILS = 5

_fails: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def _purge(key: str, now: float) -> None:
    _fails[key] = [t for t in _fails[key] if now - t < WINDOW_SEC]


def is_blocked(key: str) -> tuple[bool, int]:
    """Returns (blocked, seconds_left). seconds_left = Restzeit bis erlaubt
    falls blocked, sonst 0."""
    with _lock:
        now = time.time()
        _purge(key, now)
        if len(_fails[key]) < MAX_FAILS:
            return False, 0
        oldest_in_block = min(_fails[key])
        wait = int(WINDOW_SEC - (now - oldest_in_block))
        return True, max(wait, 1)


def record_fail(key: str) -> None:
    with _lock:
        now = time.time()
        _purge(key, now)
        _fails[key].append(now)


def reset(key: str) -> None:
    """Bei erfolgreichem Login Counter zuruecksetzen."""
    with _lock:
        _fails.pop(key, None)
