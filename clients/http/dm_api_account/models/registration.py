from pydantic import BaseModel, Field, ConfigDict

class Registration(BaseModel):
    model_config = ConfigDict(extra='forbid')           # defines how to handle keys which are not descripbed in the model
    login: str = Field(..., description='Login')        # '...' makes the field required
    password: str = Field(..., description='Password')
    email: str = Field(..., description='Email')