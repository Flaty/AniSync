from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
