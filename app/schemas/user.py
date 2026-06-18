from pydantic import BaseModel

class UserRegister(BaseModel):
    name: str
    phone: str
    password: str

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