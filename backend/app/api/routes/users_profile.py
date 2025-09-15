"""User profile management API endpoints."""

from fastapi import APIRouter, HTTPException

from app import crud, models
from app.api.deps import SessionDep
from app.constants import BAD_REQUEST_CODE, CONFLICT_CODE, FORBIDDEN_CODE
from app.core.security import get_password_hash, verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me")
def update_user_me(
    *,
    session: SessionDep,
    user_in: models.UserUpdateMe,
    current_user: models.User,
) -> models.UserPublic:
    """Update own user."""
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=CONFLICT_CODE,
                detail="User with this email already exists",
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return models.UserPublic.model_validate(current_user)


@router.patch("/me/password")
def update_password_me(
    *,
    session: SessionDep,
    body: models.UpdatePassword,
    current_user: models.User,
) -> models.Message:
    """Update own password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=BAD_REQUEST_CODE, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="New password cannot be the same as the current one",
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return models.Message(message="Password updated successfully")


@router.get("/me")
def read_user_me(current_user: models.User) -> models.UserPublic:
    """Get current user."""
    return models.UserPublic.model_validate(current_user)


@router.delete("/me")
def delete_user_me(
    session: SessionDep,
    current_user: models.User,
) -> models.Message:
    """Delete own user."""
    if current_user.is_superuser:
        raise HTTPException(
            status_code=FORBIDDEN_CODE,
            detail="Super users are not allowed to delete themselves",
        )
    session.delete(current_user)
    session.commit()
    return models.Message(message="User deleted successfully")
