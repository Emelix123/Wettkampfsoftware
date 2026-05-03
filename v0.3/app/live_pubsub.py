"""Mini-Pubsub fuer Live-Updates ueber WebSockets.

Konzept:
  * Pro Wettkampf-ID gibt's eine Menge von asyncio.Queues (eine pro
    verbundenem Client).
  * Wenn die Eingabe-Route einen Score speichert, ruft sie publish(wid)
    auf -> jeder Listener bekommt eine Nachricht in seine Queue.
  * Der WebSocket-Endpunkt blockt auf q.get() und schickt jede Nachricht
    raus. Die Clients verwenden das als Trigger fuer einen normalen
    HTMX-GET der das Rangliste-Fragment neu laedt.
  * Asyncio-only — bei FastAPI/Uvicorn (was wir benutzen) immer im
    Event-Loop, also passt das.

Vorteil vs. Polling:
  * Lokales LAN: Update kommt instant statt nach bis zu 5s.
  * WAN/Cloud: weniger Last (1 persistente WS statt N Polls/Min/Client).
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict


class WettkampfChannel:
    def __init__(self) -> None:
        # wettkampf_id -> set[Queue]
        self._listeners: DefaultDict[int, set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, wid: int) -> asyncio.Queue:
        async with self._lock:
            q: asyncio.Queue = asyncio.Queue(maxsize=10)
            self._listeners[wid].add(q)
        return q

    async def unsubscribe(self, wid: int, q: asyncio.Queue) -> None:
        async with self._lock:
            self._listeners[wid].discard(q)
            if not self._listeners[wid]:
                del self._listeners[wid]

    async def publish(self, wid: int, msg: str = "update") -> None:
        async with self._lock:
            queues = list(self._listeners.get(wid, ()))
        for q in queues:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                # Wenn ein Client extrem langsam ist, ueberspringen wir ihn.
                # Beim naechsten Update bekommt er den dann.
                pass


CHANNEL = WettkampfChannel()


def publish_update_sync(wid: int, msg: str = "update") -> None:
    """Sync-Wrapper damit auch sync-Routen publishen koennen ohne await.
    Schedult die Coroutine im laufenden Event-Loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # kein Loop -> z.B. CLI-Aufrufe wie create_admin.py
    loop.create_task(CHANNEL.publish(wid, msg))
