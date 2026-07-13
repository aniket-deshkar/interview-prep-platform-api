from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from interview_prep.api.dependencies import CurrentUser, SessionDep, SettingsDep
from interview_prep.core.security import (
    TokenType,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from interview_prep.models.entities import User
from interview_prep.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _token_pair(user: User, settings: SettingsDep) -> TokenPair:
    return TokenPair(
        access_token=create_token(user.id, TokenType.ACCESS, settings),
        refresh_token=create_token(user.id, TokenType.REFRESH, settings),
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, session: SessionDep, settings: SettingsDep
) -> TokenPair:
    email = payload.email.lower()
    exists = await session.scalar(select(User.id).where(func.lower(User.email) == email))
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        )
    user = User(
        email=email, password_hash=hash_password(payload.password), full_name=payload.full_name
    )
    session.add(user)
    await session.flush()
    return _token_pair(user, settings)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, session: SessionDep, settings: SettingsDep) -> TokenPair:
    user = await session.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _token_pair(user, settings)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: SessionDep, settings: SettingsDep) -> TokenPair:
    try:
        user_id = decode_token(payload.refresh_token, TokenType.REFRESH, settings)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from None
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
    return _token_pair(user, settings)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        target_roles=user.target_roles,
    )
