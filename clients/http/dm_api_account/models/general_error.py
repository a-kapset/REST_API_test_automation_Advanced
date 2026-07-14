from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GeneralError(BaseModel):
    """General error DTO model as declared in swagger (schemas/GeneralError)."""

    model_config = ConfigDict(extra="forbid")
    message: Optional[str] = Field(None, description="Client message")
