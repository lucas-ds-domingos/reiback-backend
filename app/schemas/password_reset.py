from pydantic import BaseModel, EmailStr
from datetime import datetime

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetCreate(BaseModel):
    token: str
    nova_senha: str

class PasswordResetResponse(BaseModel):
    message: str

class PasswordResetDB(BaseModel):
    id: int
    user_id: int
    token: str
    expires_at: datetime

    class Config:
        orm_mode = True
