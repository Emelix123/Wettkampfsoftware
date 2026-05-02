# Wettkampfsoftware v0.3

Komplette Webapp zur Wettkampf-Verwaltung — Stammdaten, Anmeldung, Live-Eingabe
mit mehreren Kampfrichtern, oeffentliche Live-Rangliste und PDF-Exports
(Startliste, Ergebnisse, Urkunden). Alles im Browser, kein SQL-Editor und keine
Word/Excel-Vorlagen mehr noetig.

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2 + bcrypt
- **Frontend:** Server-rendered Jinja2 + Tailwind (CDN) + HTMX (CDN) — kein npm/Build
- **DB:** MySQL 8
- **PDF:** WeasyPrint
- **Reverse Proxy:** nginx
- **Deploy:** docker-compose

## Schnellstart

```bash
cd v0.3
cp .env.example .env          # Passwoerter anpassen!
docker compose up --build -d
```

Browser: <http://localhost:8080>
Login: `admin` / `admin123` (wird beim ersten Start angelegt — bitte sofort aendern unter `Admin → Benutzer`).

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

## Features

| Bereich            | Was es kann                                                                  |
|--------------------|-------------------------------------------------------------------------------|
| **Stammdaten**     | Vereine, Altersklassen, Geraete, Berechnungs-Arten, Benutzer (4 Rollen)      |
| **Wettkaempfe**    | Wettkampftage → Wettkaempfe → Geraete-Zuordnung mit Berechnungs-Regel       |
| **Riegen + Teams** | Startgruppen mit Startzeit; Mannschaften mit "beste N gewerteten Mitglieder" |
| **Anmeldung**      | Personen anmelden, Startnummern, Riege/Mannschaft, Status (DQ/Rueckzug)      |
| **Eingabe**        | Tisch-Modus (alle Richter-Wertungen auf einer Maske) + Single-Modus          |
| **Live-Ansicht**   | Oeffentlich, kein Login, mobile-friendly, auto-refresh per HTMX             |
| **PDF-Export**     | Startliste, Ergebnisse, Urkunden je Wettkampf + Tag-Gesamt-PDF              |

## Rollen

- `admin`         — alles
- `tisch`         — Anmeldungen + Eingabe (Tisch-Modus, traegt fuer mehrere Richter ein)
- `kampfrichter`  — Eingabe (Single-Modus, eigene Wertung pro Versuch)
- `viewer`        — nur lesen

## Eigene Sportarten / neue Berechnungs-Arten

Score-Logik liegt komplett in Python (`app/scoring/*`).
Schritte fuer eine neue Berechnung:

1. Neue Klasse `MeineRegel(ScoringStrategy)` in `app/scoring/<sport>.py`.
   `code`, `label`, `required_kriterien`, `compute()` setzen.
2. In `app/scoring/__init__.py` zur `REGISTRY` hinzufuegen.
3. Container neu starten (`docker compose restart app`).
4. Im Web unter **Admin → Berechnungs-Arten** den neuen Code als Eintrag anlegen.

Der Wettkampf kann diese Berechnung danach pro Geraet auswaehlen.

## DB-Schema

Schema in `db/01_schema.sql`, Views in `db/02_views.sql`.
Kerntabellen:

- `Wettkampf_Tag` — der Veranstaltungstag
- `Wettkampf` — eine Konkurrenz an dem Tag
- `Geraete_has_Wettkampf` — welches Geraet mit welcher Berechnungs-Regel und wie vielen Richtern
- `Personen_has_Wettkampf` — Startliste (Riege, Mannschaft, Status)
- `Einzel_Ergebnis` — ein Versuch je Person+Geraet+Versuch_Nr
- `Kampfrichter_Wertung` + `Kampfrichter_Wertung_Detail` — Multi-Judge mit Key/Value-Kriterien

Ranglisten kommen live aus den Views — keine Cache-Tabellen, die manuell synchron gehalten werden muessten.

## Lokale Entwicklung ohne Docker (optional)

```bash
cd v0.3/app
python -m venv .venv && source .venv/bin/activate    # bzw. .venv\Scripts\activate auf Windows
pip install -r requirements.txt
# DB starten, Schema laden, dann:
DB_HOST=localhost DB_PORT=3307 uvicorn main:app --reload
```

Hinweis: WeasyPrint braucht unter Windows extra Setup (GTK).
Docker ist deutlich einfacher.

## Test-Workflow (Demo-Daten)

Nach `docker compose up`:

1. Login als `admin`.
2. **Wettkampftage** → "Demo-Turnfest 2026" oeffnen.
3. **Mehrkampf Maennlich Offen** → **Eingabe** → Boden waehlen.
4. Im Tisch-Modus pro Athlet die D- und E-Noten von 3 Richtern eintragen → speichern.
5. Score erscheint sofort. Wenn weniger als 3 Richter eingetragen sind, bleibt der Versuch "in Bewertung".
6. **Live-Ansicht** in einem zweiten Browser-Tab oeffnen (kein Login noetig) → aktualisiert sich automatisch.
7. **PDF → Urkunden** generiert die Urkunden fuer alle platzierten Athleten.
