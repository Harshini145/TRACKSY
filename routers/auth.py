from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from core.config import settings
from core.database import get_db
from core.security import (
    create_access_token,
    create_password_reset_token,
    hash_password,
    verify_password,
    verify_password_reset_token,
)
from models.user import User, UserSetting, Category
from services.email_service import send_password_reset_email, send_welcome_email

router = APIRouter(prefix="/auth", tags=["Auth"])


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


# ── Signup ────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    # Default settings
    db.add(UserSetting(user_id=user.user_id, theme="light"))

    # Seed default categories
    default_cats = ["Food", "Transport", "Shopping", "Health", "Rent", "Utilities", "Education", "Entertainment"]
    for cat_name in default_cats:
        db.add(Category(user_id=user.user_id, name=cat_name))

    db.commit()
    db.refresh(user)

    # Send welcome email (fire & forget — don't block signup if SMTP fails)
    try:
        await send_welcome_email(user.email, user.username)
    except Exception as e:
        print(f"[WARN] Welcome email failed for {user.email}: {e}")

    token = create_access_token({"sub": str(user.user_id)})
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        username=user.username,
        email=user.email,
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.username).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token({"sub": str(user.user_id)})
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        username=user.username,
        email=user.email,
    )


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = create_password_reset_token(user.user_id)
        app_base_url = settings.APP_BASE_URL or str(request.base_url).rstrip("/")
        reset_link = f"{app_base_url.rstrip('/')}/app/index.html?reset_token={token}"
        try:
            await send_password_reset_email(user.email, user.username, reset_link)
        except Exception as e:
            print(f"[WARN] Password reset email failed for {user.email}: {e}")
            raise HTTPException(status_code=500, detail="Could not send password reset email")

    return {"message": "If that email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user_id = verify_password_reset_token(payload.token)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset link")

    user.password = hash_password(payload.password)
    db.commit()
    return {"message": "Password reset successful. You can now log in."}
