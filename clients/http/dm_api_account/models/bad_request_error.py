from pydantic import BaseModel, ConfigDict, Field


class BadRequestError(BaseModel):
    """Bad request error DTO as declared in swagger (schemas/BadRequestError)."""

    model_config = ConfigDict(extra="forbid")
    message: str | None = Field(None, description="Client message")
    invalid_properties: dict[str, list[str]] | None = Field(
        None,
        alias="invalidProperties",
        description="Key-value pairs of invalid request properties",
    )
