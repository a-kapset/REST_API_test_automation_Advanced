from pydantic import BaseModel, ConfigDict, Field


class LoginCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: str = Field(..., description="Login")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(..., description="Remember me", serialization_alias="rememberMe")
