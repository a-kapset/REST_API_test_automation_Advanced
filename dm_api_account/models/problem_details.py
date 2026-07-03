from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProblemDetails(BaseModel):
    """
    Actual body returned for the 403 status of POST /v1/account/login    

    NOTE: swagger declares 403 -> GeneralError, but the server really returns
    this ProblemDetails shape, so this model reflects the real API, not swagger.
    """
    
    model_config = ConfigDict(extra='forbid')
    type: Optional[str] = None
    title: Optional[str] = None
    status: Optional[int] = None
    detail: Optional[str] = None
    trace_id: Optional[str] = Field(None, alias='traceId')
