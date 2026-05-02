"""CLI-Rettungsanker: Default-Admin manuell anlegen oder Passwort
zuruecksetzen, ohne Web-UI.

Verwendung:
    docker compose exec app python create_admin.py
    docker compose exec app python create_admin.py --user emil --pass geheim123
    docker compose exec app python create_admin.py --reset-pass admin --pass neuespw
"""
import argparse
import sys

from sqlalchemy.exc import OperationalError

from auth import hash_password, ensure_default_admin
from database import SessionLocal
from models import User
import settings


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--user", default=settings.DEFAULT_ADMIN_USER,
                   help="Benutzername (Default: aus DEFAULT_ADMIN_USER)")
    p.add_argument("--pass", dest="password", default=settings.DEFAULT_ADMIN_PASS,
                   help="Passwort (Default: aus DEFAULT_ADMIN_PASS)")
    p.add_argument("--mail", default=settings.DEFAULT_ADMIN_MAIL,
                   help="E-Mail (Default: aus DEFAULT_ADMIN_MAIL)")
    p.add_argument("--reset-pass", metavar="USERNAME",
                   help="Nur das Passwort eines bestehenden Users zuruecksetzen.")
    args = p.parse_args()

    db = SessionLocal()
    try:
        if args.reset_pass:
            u = db.query(User).filter(User.username == args.reset_pass).first()
            if not u:
                print(f"User '{args.reset_pass}' nicht gefunden.")
                return 2
            u.password_hash = hash_password(args.password)
            u.is_active = 1
            db.commit()
            print(f"OK — Passwort von '{u.username}' zurueckgesetzt.")
            return 0

        # Anlegen oder Update
        u = db.query(User).filter(User.username == args.user).first()
        if u:
            u.password_hash = hash_password(args.password)
            u.email = args.mail
            u.role = "admin"
            u.is_active = 1
            db.commit()
            print(f"OK — User '{u.username}' aktualisiert (admin, aktiv).")
            print(f"   Login: {args.user} / {args.password}")
            return 0

        u = User(
            username=args.user,
            email=args.mail,
            password_hash=hash_password(args.password),
            role="admin",
            is_active=1,
        )
        db.add(u)
        db.commit()
        print(f"OK — neuer Admin angelegt.")
        print(f"   Login: {args.user} / {args.password}")
        return 0
    except OperationalError as e:
        print(f"DB-Verbindung fehlgeschlagen: {e}")
        print("Laeuft 'db' im docker compose? -> docker compose ps")
        return 3
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
