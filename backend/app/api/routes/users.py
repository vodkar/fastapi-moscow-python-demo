"""User management API endpoints - consolidated router."""

from fastapi import APIRouter

from app.api.routes.users_admin import router as admin_router
from app.api.routes.users_auth import router as auth_router
from app.api.routes.users_profile import router as profile_router

router = APIRouter()

router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(profile_router)
