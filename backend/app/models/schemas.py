from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = Field(default=None, gt=0)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be blank")
        return value


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []
    images: list[str] = []
    conversation_id: int


class UploadResponse(BaseModel):
    filename: str
    chunks_added: int


class SourceListResponse(BaseModel):
    sources: list[str]


class ImageRequest(BaseModel):
    prompt: str


class ImageResponse(BaseModel):
    prompt: str
    image_base64: str
    mime_type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    full_name: str | None = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: str
    images: str
    created_at: datetime

    class Config:
        from_attributes = True
