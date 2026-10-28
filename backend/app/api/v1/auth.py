from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import CurrentUser, create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import DbSession
from app.schemas.auth import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

# Unknown-email logins still run one bcrypt check, so response time doesn't reveal which emails exist
_DUMMY_HASH = hash_password("timing-equalizer")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: DbSession) -> User:
    # bcrypt is CPU-bound (~200ms); run it off the event loop so other requests keep flowing
    hashed = await run_in_threadpool(hash_password, body.password)
    user = User(email=body.email, hashed_password=hashed, full_name=body.full_name)
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None
    return user


@router.post("/login", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> Token:
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    password_ok = await run_in_threadpool(
        verify_password, form.password, user.hashed_password if user else _DUMMY_HASH
    )
    if user is None or not password_ok or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> User:
    return user
