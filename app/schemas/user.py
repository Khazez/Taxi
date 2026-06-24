from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    name: str
    phone: str
    password: str
    role: Optional[str] = "passenger"  # "passenger" или "driver"

class UserLogin(BaseModel):
    phone: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    role: str

    class Config:
        from_attributes = True