from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.security import hash_password, verify_password, create_access_token
from models.user import User, UserSetting, Category
from services.email_service import send_welcome_email

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
    except Exception:
        pass

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
