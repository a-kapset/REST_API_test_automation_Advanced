from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from clients.http.dm_api_account.models.user_envelope import Rating, UserRole


class BbParseMode(str, Enum):
    COMMON = "Common"
    INFO = "Info"
    POST = "Post"
    CHAT = "Chat"


class ColorSchema(str, Enum):
    MODERN = "Modern"
    PALE = "Pale"
    CLASSIC = "Classic"
    CLASSIC_PALE = "ClassicPale"
    NIGHT = "Night"


class InfoBbText(BaseModel):
    value: Optional[str] = None
    parse_mode: Optional[BbParseMode] = Field(None, alias="parseMode")


class PagingSettings(BaseModel):
    posts_per_page: Optional[int] = Field(None, alias="postsPerPage")
    comments_per_page: Optional[int] = Field(None, alias="commentsPerPage")
    topics_per_page: Optional[int] = Field(None, alias="topicsPerPage")
    messages_per_page: Optional[int] = Field(None, alias="messagesPerPage")
    entities_per_page: Optional[int] = Field(None, alias="entitiesPerPage")


class UserSettings(BaseModel):
    color_schema: Optional[ColorSchema] = Field(None, alias="colorSchema")
    nanny_greetings_message: Optional[str] = Field(None, alias="nannyGreetingsMessage")
    paging: Optional[PagingSettings] = None


class UserDetails(BaseModel):
    login: Optional[str] = None
    roles: List[UserRole]
    medium_picture_url: Optional[str] = Field(None, alias="mediumPictureUrl")
    small_picture_url: Optional[str] = Field(None, alias="smallPictureUrl")
    status: Optional[str] = Field(None, alias="status")
    rating: Rating
    online: Optional[datetime] = Field(None, alias="online")
    name: Optional[str] = Field(None, alias="name")
    location: Optional[str] = Field(None, alias="location")
    registration: Optional[datetime] = None
    icq: Optional[str] = Field(None, alias="icq")
    skype: Optional[str] = Field(None, alias="skype")
    original_picture_url: Optional[str] = Field(None, alias="originalPictureUrl")
    info: Optional[InfoBbText] = None
    settings: Optional[UserSettings] = None

    @field_validator("info", mode="before")
    @classmethod
    def _empty_info_to_none(cls, value):
        # The API serializes an absent InfoBbText as an empty string rather than
        # null/object; normalize it so it matches the schema's object type.
        if value == "":
            return None
        return value


class UserDetailsEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resource: Optional[UserDetails] = None
    metadata: Optional[Any] = None
