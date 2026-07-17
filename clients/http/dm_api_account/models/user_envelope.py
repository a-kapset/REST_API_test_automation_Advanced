from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class UserRole(StrEnum):
    GUEST = "Guest"
    PLAYER = "Player"
    ADMINISTRATOR = "Administrator"
    NANNY_MODERATOR = "NannyModerator"
    REGULAR_MODERATOR = "RegularModerator"
    SENIOR_MODERATOR = "SeniorModerator"


class Rating(BaseModel):
    enabled: bool
    quality: int
    quantity: int


class User(BaseModel):
    login: str
    roles: list[UserRole]
    medium_picture_url: str | None = Field(None, alias="mediumPictureUrl")
    small_picture_url: str | None = Field(None, alias="smallPictureUrl")
    status: str | None = Field(None, alias="status")
    rating: Rating
    online: datetime | None = Field(None, alias="online")
    name: str | None = Field(None, alias="name")
    location: str | None = Field(None, alias="location")
    registration: datetime | None = None


class UserEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resource: User | None = None
    # swagger declares metadata with a description and nullable: true, but no type
    # at all, so the contract really does allow any shape here. `object` says that
    # without the side effect of `Any`, which would silently disable checking on
    # every expression it touches.
    metadata: object | None = None
