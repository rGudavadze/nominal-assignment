from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AccountBase(BaseModel):
    name: str
    classification: Optional[str] = None
    currency_ref: Optional[str] = None
    account_type: Optional[str] = None
    active: bool = True
    current_balance: Optional[float] = None
    parent_id: Optional[str] = None


class AccountCreate(AccountBase):
    qbo_id: str


class Account(AccountBase):
    id: int
    qbo_id: str
    last_synced_at: datetime
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True

# This is needed for the self-referential relationship in Account
Account.model_rebuild()
