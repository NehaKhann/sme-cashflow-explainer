import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..db_models import User
from ..auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    validate_refresh_token, revoke_refresh_token,
    get_current_user,
)
from ..rate_limit import limiter

logger = logging.getLogger("cashflow_explainer")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str


@router.post("/signup", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
async def signup(request: Request, body: SignupRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name or body.email.split("@")[0],
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered.")
    await db.refresh(user)

    user_id_str = str(user.id)
    return TokenResponse(
        access_token=create_access_token(user_id_str, user.email),
        refresh_token=await create_refresh_token(user_id_str, user.email, db),
        user={"id": user_id_str, "email": user.email, "display_name": user.display_name},
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user_id_str = str(user.id)
    return TokenResponse(
        access_token=create_access_token(user_id_str, user.email),
        refresh_token=await create_refresh_token(user_id_str, user.email, db),
        user={"id": user_id_str, "email": user.email, "display_name": user.display_name},
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh(request: Request, body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = await validate_refresh_token(body.refresh_token, db)

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    await revoke_refresh_token(body.refresh_token, db)

    return TokenResponse(
        access_token=create_access_token(user_id, email),
        refresh_token=await create_refresh_token(user_id, email, db),
        user={"id": user_id, "email": email, "display_name": ""},
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
    )
