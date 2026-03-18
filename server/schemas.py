from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    is_admin: bool = False


class UserChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class AdminChangePasswordRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    new_password: str = Field(min_length=6, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool
    created_at: datetime


class UserPresenceOut(BaseModel):
    username: str
    online: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserPublic


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class MessageOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    username: str


class StatsOut(BaseModel):
    users_total: int
    messages_total: int
