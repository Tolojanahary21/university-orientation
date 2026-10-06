from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str | None
    last_name: str | None
    role: UserRole
    is_active: bool
    email_verified_at: datetime | None
    created_at: datetime