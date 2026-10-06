from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
)
from pydantic import (
    Field as PydanticField,
)


class FieldCreate(BaseModel):
    code: str = PydanticField(
        min_length=1,
        max_length=30,
    )

    name: str = PydanticField(
        min_length=1,
        max_length=150,
    )

    description: str | None = None

    category: str | None = PydanticField(
        default=None,
        max_length=100,
    )

    requirements: dict | None = None


class FieldUpdate(BaseModel):
    code: str | None = PydanticField(
        default=None,
        min_length=1,
        max_length=30,
    )

    name: str | None = PydanticField(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = None

    category: str | None = PydanticField(
        default=None,
        max_length=100,
    )

    requirements: dict | None = None


class FieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str

    description: str | None
    category: str | None
    requirements: dict | None

    is_active: bool

    created_at: datetime
    updated_at: datetime
