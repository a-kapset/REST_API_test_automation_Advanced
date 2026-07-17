from pydantic import BaseModel, ConfigDict, Field


class ResetPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: str = Field(..., description="Login")
    email: str = Field(..., description="Email")
