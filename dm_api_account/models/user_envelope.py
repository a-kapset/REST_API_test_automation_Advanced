from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class UserRole(str, Enum):
    GUEST = 'Guest'
    PLAYER = 'Player'
    ADMINISTRATOR = 'Administrator'
    NANNY_MODERATOR = 'NannyModerator'
    REGULAR_MODERATOR = 'RegularModerator'
    SENIOR_MODERATOR = 'SeniorModerator'


class Rating(BaseModel):
    enabled: bool
    quality: int
    quantity: int


class User(BaseModel):
    login: str
    roles: List[UserRole]
    medium_picture_url: Optional[str] = Field(None, alias='mediumPictureUrl')
    small_picture_url: Optional[str] = Field(None, alias='smallPictureUrl')
    status: Optional[str] = Field(None, alias='status')
    rating: Rating
    online: Optional[datetime] = Field(None, alias='online')
    name: Optional[str] = Field(None, alias='name')
    location: Optional[str] = Field(None, alias='location')
    registration: Optional[datetime] = None


class UserEnvelope(BaseModel):
    model_config = ConfigDict(extra='forbid')
    resource: Optional[User] = None
    metadata: Optional[Any] = None
