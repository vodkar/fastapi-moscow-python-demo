"""User authentication API endpoints."""

from fastapi import APIRouter, HTTPException

from app import crud, models
from app.api.deps import SessionDep
from app.constants import BAD_REQUEST_CODE

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup")
def register_user(
    session: SessionDep,
    user_in: models.UserRegister,
) -> models.UserPublic:
    """Create new user without the need to be logged in."""
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="The user with this email already exists in the system",
        )
    user_create = models.UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return models.UserPublic.model_validate(user)
