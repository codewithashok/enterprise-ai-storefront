from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Request body for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def fits_bcrypt_limit(cls, value: str) -> str:
        # bcrypt reads at most 72 *bytes*; emoji/non-ASCII chars use 2-4 bytes each
        if len(value.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return value


class UserRead(BaseModel):
    """Public user shape — the only user fields that ever leave the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
