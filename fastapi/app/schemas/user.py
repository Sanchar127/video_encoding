from pydantic import BaseModel, EmailStr, HttpUrl, Field
from uuid import UUID

class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Email is automatically validated by Pydantic
    password: str
    mobile: str
    address: str
    role: str = Field(default="user", pattern="^(user|admin|super_admin)$")  # Regex for role validation
    is_activated: bool = True
    status: bool = True
    stream_url: HttpUrl  # This will validate that it's an HTTP/HTTPS URL
    callback_key: str
    callback_url: HttpUrl  # This will validate that it's an HTTP/HTTPS URL
    callback_secret_key: str
    email_notification_status: bool = True
    email_notification: bool = True

  

class UserOut(BaseModel):
    id: int
    unique_id: UUID
    name: str
    email: EmailStr
    role: str
    is_activated: bool
    status: bool
    mobile: str
    address: str
    stream_url: HttpUrl  # This will validate that it's an HTTP/HTTPS URL
    callback_key: str
    callback_url: HttpUrl  # This will validate that it's an HTTP/HTTPS URL
    callback_secret_key: str
    email_notification_status: bool = True
    email_notification: bool = True

    class Config:
        orm_mode = True

