from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Passe Zugangsdaten an: user:password@host/dbname
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost/wettkampfDB"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency für FastAPI (stellt sicher, dass DB nach Request geschlossen wird)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()