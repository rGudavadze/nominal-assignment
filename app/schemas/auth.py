from pydantic import BaseModel
from datetime import datetime


class TokenBase(BaseModel):
    access_token: str
    refresh_token: str
    realm_id: str
    expires_at: datetime

class TokenCreate(TokenBase):
    expires_in: int

class Token(TokenBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
