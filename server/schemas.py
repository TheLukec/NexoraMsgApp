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
    content: str = Field(default="", max_length=1000)
    parent_message_id: int | None = Field(default=None, ge=1)


class ReplyToOut(BaseModel):
    id: int | None
    author: str
    content: str
    deleted: bool = False


class MessageAttachmentOut(BaseModel):
    id: int | None = None
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    file_download_path: str | None = None
    available: bool = True
    availability_message: str | None = None


class MessageOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    username: str
    parent_message_id: int | None = None
    reply_to: ReplyToOut | None = None

    attachments: list[MessageAttachmentOut] = Field(default_factory=list)

    # Legacy fields remain for compatibility with older clients.
    file_name: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    file_download_path: str | None = None


class StatsOut(BaseModel):
    users_total: int
    messages_total: int


class UploadLimitOut(BaseModel):
    max_upload_mb: int
    uploads_enabled: bool
