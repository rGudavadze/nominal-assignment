from pydantic import BaseModel
from typing import Optional


class AccountBaseSchema(BaseModel):
    qbo_id: str
    name: str
    classification: Optional[str] = None
    currency_ref: Optional[str] = None
    account_type: Optional[str] = None
    active: bool = True
    current_balance: Optional[float] = None
    parent_id: Optional[str] = None


class AccountCreateSchema(AccountBaseSchema):
    pass


class AccountSchema(AccountBaseSchema):
    id: int

    class Config:
        from_attributes = True

# This is needed for the self-referential relationship in Account
AccountSchema.model_rebuild()
