from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BadRequestError(BaseModel):
    """Bad request error DTO as declared in swagger (schemas/BadRequestError)."""

    model_config = ConfigDict(extra="forbid")
    message: Optional[str] = Field(None, description="Client message")
    invalid_properties: Optional[Dict[str, List[str]]] = Field(
        None,
        alias="invalidProperties",
        description="Key-value pairs of invalid request properties",
    )
