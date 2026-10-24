import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import Admin


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> Admin | None:
        stmt = select(Admin).where(Admin.email == email.lower())
        return self.db.scalars(stmt).first()

    def get(self, admin_id: uuid.UUID) -> Admin | None:
        return self.db.get(Admin, admin_id)

    def create(self, admin: Admin) -> Admin:
        self.db.add(admin)
        self.db.flush()
        return admin
