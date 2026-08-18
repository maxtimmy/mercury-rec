"""Versioned contracts at the data boundary."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserEventV1(BaseModel):
    """Canonical event accepted by the future stream consumer."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    schema_version: Literal[1] = 1
    user_id: str = Field(min_length=1, max_length=128)
    item_id: str = Field(min_length=1, max_length=128)
    event_type: Literal["purchase"]
    event_time: datetime
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    source: str = Field(min_length=1, max_length=64)
