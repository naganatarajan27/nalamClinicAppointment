from fastapi import APIRouter

from app.api.v1 import admin_appointments, admin_auth, admin_doctors, public, webhooks

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(public.router)
api_router.include_router(admin_auth.router)
api_router.include_router(admin_appointments.read_router)
api_router.include_router(admin_appointments.router)
api_router.include_router(admin_doctors.router)
api_router.include_router(webhooks.router)
