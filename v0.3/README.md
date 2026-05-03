# Wettkampfsoftware v0.3

Komplette Webapp zur Wettkampf-Verwaltung — Stammdaten, Anmeldung, Live-Eingabe
mit mehreren Kampfrichtern, oeffentliche Live-Rangliste mit Detail-Ansicht und
PDF-Exporte (Startliste, Ergebnisse, Urkunden, Wertungskarten). Audit-Log,
JSON-Backup und CSV-Export inklusive. Alles im Browser, kein SQL-Editor und
keine Word/Excel-Vorlagen mehr noetig.

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2 + bcrypt
- **Frontend:** Server-rendered Jinja2 + Tailwind (CDN) + HTMX (CDN) + WebSocket — kein npm/Build
- **DB:** MySQL 8
- **PDF:** WeasyPrint
- **Reverse Proxy:** nginx (mit WebSocket-Upgrade)
- **Deploy:** docker-compose

## Schnellstart

```bash
cd v0.3
cp .env.example .env          # Passwoerter anpassen!
docker compose up --build -d
```

Browser: <http://localhost:8080>
Login: `admin` / `admin123` (wird beim ersten Start angelegt — sofort aendern unter Admin → Benutzer).

DB-Port (fuer DBeaver o.ae.): `localhost:3307`

### Logs ansehen

```bash
docker compose logs -f app
```

### Stoppen / neu starten

```bash
docker compose down            # behaelt die DB-Daten
docker compose down -v         # loescht ALLES inkl. DB
```

### Update auf neue Version (ohne DB-Verlust)

```bash
git pull
docker compose up -d --build
```

Schema-Migrationen (Audit-Tabelle, Logo-Spalten) sind als idempotente
SQL-Scripts (`db/04_audit.sql`, `db/05_logos.sql`) eingebaut — laufen
automatisch beim Start des DB-Containers. Existierende Daten bleiben.

## Features

| Bereich            | Was es kann                                                                  |
|--------------------|-------------------------------------------------------------------------------|
| **Stammdaten**     | Vereine (mit Logo), Altersklassen, Geraete, Berechnungs-Arten, Benutzer (4 Rollen) — alle inline editierbar |
| **Wettkaempfe**    | Wettkampftage (mit Logo) → Wettkaempfe → Geraete-Zuordnung mit Berechnungs-Regel, Reihenfolge per ▲▼-Buttons |
| **Riegen + Teams** | Startgruppen mit Startzeit; Mannschaften mit "beste N gewerteten Mitglieder" |
| **Anmeldung**      | Personen anmelden, Startnummern, Riege/Mannschaft, Status (DQ/Rueckzug mit Begruendung) |
| **Massen-Import**  | CSV-Upload mit Vorschau-Modus, Auto-Vereins-Anlage |
| **Eingabe**        | Tisch-Modus (alle Richter-Wertungen auf einer Maske) + Single-Modus (eigene Wertung) — einzelne Slots loeschbar/editierbar |
| **Live-Ansicht**   | Oeffentlich, kein Login, mobile-friendly, **WebSocket-Push** (Update kommt instant), Per-Geraet-Spalten |
| **Live-Detail**    | Klick auf Athlet → alle Versuche mit Aufschluesselung pro Richter |
| **Riegen-Status**  | Wer ist wo? Pro Riege/Geraet wieviele Mitglieder schon fertig sind |
| **Athleten-Profil**| Alle Wettkampf-Teilnahmen, Platzierung und Score |
| **PDF-Export**     | Startliste, Ergebnisse, Urkunden (auch Top-N), leere **Wertungskarten** je Geraet, Tag-Gesamt-PDF — Logos werden eingebettet |
| **CSV-Export**     | Ergebnisse pro Wettkampf als UTF-8-CSV (Excel-freundlich) |
| **Audit-Log**      | Wer hat wann welchen Score eingetragen / geaendert / geloescht |
| **JSON-Backup**    | Vollstaendiger Snapshot eines Wettkampftags zum Download |
| **Auto-Logout**    | Nach 60 Min Inaktivitaet (konfigurierbar via SESSION_MAX_AGE) |
| **CSRF-Schutz**    | Auf allen POST-Forms |

## Rollen

- `admin`         — alles
- `tisch`         — Anmeldungen + Eingabe (Tisch-Modus, traegt fuer mehrere Richter ein)
- `kampfrichter`  — Eingabe (Single-Modus, eigene Wertung pro Versuch — eigener Slot wird automatisch vergeben)
- `viewer`        — nur lesen

## Eigene Sportarten / neue Berechnungs-Arten

Score-Logik liegt komplett in Python (`app/scoring/*`).
Schritte fuer eine neue Berechnung:

1. Neue Klasse `MeineRegel(ScoringStrategy)` in `app/scoring/<sport>.py`.
   `code`, `label`, `required_kriterien`, `compute()` setzen.
2. In `app/scoring/__init__.py` zur `REGISTRY` hinzufuegen.
3. Container neu starten (`docker compose restart app`).
4. Im Web unter **Admin → Berechnungs-Arten** den neuen Code als Eintrag anlegen.

Der Wettkampf kann diese Berechnung danach pro Geraet auswaehlen. Wenn du
nach dem ersten Eingeben den Faktor / Offset / die Berechnungs-Art
aenderst, werden alle bestehenden Versuche **automatisch neu durchgerechnet**.

## DB-Schema

- `01_schema.sql` — Tabellen
- `02_views.sql` — Live-Ranglisten als Views (kein Cache zu pflegen)
- `03_seed.sql` — Default-Stammdaten (Berechnungs-Arten, Altersklassen, Geraete)
- `04_audit.sql` — Audit-Tabelle (idempotente Migration)
- `05_logos.sql` — Logo-Spalten (idempotente Migration)
- `99_demo_data.sql` — optional, Demo-Daten (Wettkampftag mit Athleten, Mannschaft, Riege)

## Live-Scoring im Detail

- **WebSocket** `/live/wettkampf/{wid}/ws`: jede Eingabe pusht ein "update"
  an alle verbundenen Tabs, die laden dann via HTMX-GET das Rangliste-Fragment neu.
- Backup-Polling alle 30 Sek falls WebSocket scheitert (Proxy-Probleme).
- Auto-Reconnect mit Exponential-Backoff (1s → max 10s).
- Status-Indikator (gruen/gelb/grau) im Live-Header.

## Backup-Empfehlung

Vor jedem Wettkampfstart **und** nach dem Wettkampf:

1. Im Admin-Bereich `→ Backup` den Wettkampftag auswaehlen.
2. JSON herunterladen, auf einem zweiten Geraet ablegen.
3. Bei Datenverlust kann die JSON-Datei als Beweisstueck dienen — automatischer
   Restore ist nicht eingebaut, aber das Format ist klar genug fuer manuelle
   Wiederherstellung per Hand oder Script.

Zusaetzlich oder alternativ: das DB-Volume sichern via
`docker run --rm -v v03_db_data:/data -v $(pwd):/backup ubuntu tar czf /backup/db.tgz /data`.

## Test-Workflow (Demo-Daten)

Nach `docker compose up`:

1. Login als `admin` / `admin123`.
2. **Wettkampftage** → "Demo-Turnfest 2026" oeffnen.
3. **Mehrkampf Maennlich Offen** → **Eingabe** → Boden waehlen.
4. Im Tisch-Modus pro Athlet die D- und E-Noten von 3 Richtern eintragen → speichern.
5. Score erscheint sofort. Wenn weniger als 3 Richter eingetragen sind, bleibt der Versuch "in Bewertung".
6. **Live-Ansicht** in einem zweiten Browser-Tab oeffnen (kein Login noetig) → aktualisiert sich automatisch via WebSocket.
7. Klick auf einen Athletennamen → Detail-Ansicht mit allen Wertungen je Richter.
8. **PDF → Urkunden** generiert die Urkunden fuer alle platzierten Athleten.

## Notfall: Admin-Passwort vergessen

```bash
docker compose exec app python create_admin.py --reset-pass admin --pass neuespw
```
