import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    csrf_token: str


class AdminMe(BaseModel):
    id: uuid.UUID
    email: EmailStr
