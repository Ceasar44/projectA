from pydantic import BaseModel, ConfigDict, Field

from app.domain.shared.enums import Role


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class SetupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=200)
    name: str | None = Field(default=None, max_length=200)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    name: str
    role: Role


class AuthStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    authenticated: bool
    setup_required: bool = Field(alias="setupRequired")
    user: UserResponse | None


class AuthContext(BaseModel):
    user_id: str
    username: str
    name: str
    role: Role
    auth_method: str
