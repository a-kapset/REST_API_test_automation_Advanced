from pydantic import BaseModel, ConfigDict, Field


class ProblemDetails(BaseModel):
    """
    Actual body returned for the 403 status of POST /v1/account/login

    NOTE: swagger declares 403 -> GeneralError, but the server really returns
    this ProblemDetails shape, so this model reflects the real API, not swagger.
    """

    model_config = ConfigDict(extra="forbid")
    type: str | None = None
    title: str | None = None
    status: int | None = None
    detail: str | None = None
    trace_id: str | None = Field(None, alias="traceId")
