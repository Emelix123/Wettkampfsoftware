# Wähle ein passendes Python-Basisimage
FROM python:3.9-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere Systemabhängigkeiten für pandas und Excel (z. B. xlsxwriter und openpyxl)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libatlas-base-dev \
    libffi-dev \
    libssl-dev \
 && rm -r /var/lib/apt/lists/*

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir pandas xlsxwriter openpyxl flask mysql-connector-python gunicorn


# Kopiere die Abhängigkeitsdatei und installiere sie
COPY requirements.txt .

# --no-cache-dir spart Speicherplatz im Image
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Anwendungscodes in das Arbeitsverzeichnis
COPY . .

# Befehl zum Starten der Anwendung bei Containerstart
# Verwende Gunicorn als WSGI-Server (besser für Produktion als der Flask Dev Server)
# 'app:app' bedeutet: Suche in der Datei 'app.py' nach einer Variable namens 'app'
# Passe 'app:app' an, falls deine Flask-Instanz anders heißt oder in einer anderen Datei liegt
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
