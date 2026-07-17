from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from clients.http.dm_api_account.models.user_envelope import Rating, UserRole


class BbParseMode(StrEnum):
    COMMON = "Common"
    INFO = "Info"
    POST = "Post"
    CHAT = "Chat"


class ColorSchema(StrEnum):
    MODERN = "Modern"
    PALE = "Pale"
    CLASSIC = "Classic"
    CLASSIC_PALE = "ClassicPale"
    NIGHT = "Night"


class InfoBbText(BaseModel):
    value: str | None = None
    parse_mode: BbParseMode | None = Field(None, alias="parseMode")


class PagingSettings(BaseModel):
    posts_per_page: int | None = Field(None, alias="postsPerPage")
    comments_per_page: int | None = Field(None, alias="commentsPerPage")
    topics_per_page: int | None = Field(None, alias="topicsPerPage")
    messages_per_page: int | None = Field(None, alias="messagesPerPage")
    entities_per_page: int | None = Field(None, alias="entitiesPerPage")


class UserSettings(BaseModel):
    color_schema: ColorSchema | None = Field(None, alias="colorSchema")
    nanny_greetings_message: str | None = Field(None, alias="nannyGreetingsMessage")
    paging: PagingSettings | None = None


class UserDetails(BaseModel):
    login: str | None = None
    roles: list[UserRole]
    medium_picture_url: str | None = Field(None, alias="mediumPictureUrl")
    small_picture_url: str | None = Field(None, alias="smallPictureUrl")
    status: str | None = Field(None, alias="status")
    rating: Rating
    online: datetime | None = Field(None, alias="online")
    name: str | None = Field(None, alias="name")
    location: str | None = Field(None, alias="location")
    registration: datetime | None = None
    icq: str | None = Field(None, alias="icq")
    skype: str | None = Field(None, alias="skype")
    original_picture_url: str | None = Field(None, alias="originalPictureUrl")
    info: InfoBbText | None = None
    settings: UserSettings | None = None

    @field_validator("info", mode="before")
    @classmethod
    def _empty_info_to_none(cls, value: object) -> object:
        # The API serializes an absent InfoBbText as an empty string rather than
        # null/object; normalize it so it matches the schema's object type.
        #
        # `object` rather than `Any`: a before-validator really does receive
        # arbitrary raw JSON, but `object` forces a narrowing check before the
        # value is used, whereas `Any` would silently allow any operation on it.
        if value == "":
            return None
        return value


class UserDetailsEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resource: UserDetails | None = None
    # See the note on UserEnvelope.metadata: untyped in swagger, so `object`.
    metadata: object | None = None
