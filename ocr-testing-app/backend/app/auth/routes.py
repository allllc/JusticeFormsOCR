"""
Authentication routes.
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends

from app.config import get_settings
from app.auth.utils import verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.models.user import LoginRequest, Token, UserResponse
from app.services.firestore import FirestoreService

settings = get_settings()
router = APIRouter()


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    """
    firestore = FirestoreService()

    # Get user by email
    user = await firestore.get_user_by_email(request.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout():
    """
    Logout user.
    Note: With JWT, logout is handled client-side by discarding the token.
    This endpoint is provided for API completeness.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    return current_user
