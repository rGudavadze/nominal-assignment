from pydantic import BaseModel
from datetime import datetime


class TokenBaseSchema(BaseModel):
    access_token: str
    refresh_token: str
    realm_id: str
    expires_at: datetime

class TokenCreateSchema(TokenBaseSchema):
    expires_in: int

class TokenSchema(TokenBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
