from pydantic import BaseModel, ConfigDict, Field


class GeneralError(BaseModel):
    """General error DTO model as declared in swagger (schemas/GeneralError)."""

    model_config = ConfigDict(extra="forbid")
    message: str | None = Field(None, description="Client message")
