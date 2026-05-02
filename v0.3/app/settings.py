import os

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "wettkampf")
DB_PASSWORD = os.getenv("DB_PASSWORD", "wettkampf")
DB_NAME = os.getenv("DB_NAME", "wettkampfDB")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
SESSION_COOKIE = "wk_session"

DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASS", "admin123")
DEFAULT_ADMIN_MAIL = os.getenv("DEFAULT_ADMIN_MAIL", "admin@example.com")
