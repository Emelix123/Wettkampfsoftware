from fastapi import FastAPI
from database import engine
import models
from routers import ergebnisse

# Optional: Erstellt die Tabellen, falls sie nicht existieren 
# (Da du dein SQL Script hast, kannst du das eigentlich weglassen)
# models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WettkampfDB API",
    description="Backend für die extrem flexible Wettkampfsoftware",
    version="1.0.0"
)

# API-Router einbinden
app.include_router(ergebnisse.router)
# app.include_router(wettkampf.router) # <- Später für weitere Dateien

@app.get("/")
def read_root():
    return {"message": "Wettkampf API läuft!"}