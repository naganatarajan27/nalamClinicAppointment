"""Create the first clinic administrator.

There is no public admin self-registration route, so the first admin
must be created through this script (or a future admin-to-admin invite
flow). Run from backend/ with the virtualenv active:

    python scripts/create_admin.py --email admin@example.com
"""

import argparse
import getpass
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        raise SystemExit(1)
    if len(password) < 12:
        print("Password must be at least 12 characters.", file=sys.stderr)
        raise SystemExit(1)

    db = SessionLocal()
    try:
        repo = AdminRepository(db)
        if repo.get_by_email(args.email):
            print(f"An admin with email {args.email} already exists.", file=sys.stderr)
            raise SystemExit(1)

        admin = Admin(email=args.email.lower(), password_hash=hash_password(password))
        repo.create(admin)
        db.commit()
        print(f"Created admin {args.email} ({admin.id}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
