from typing import List

from fastapi import HTTPException, Depends, APIRouter

from app.schemas.account import Account
from app.services.account import AccountService
from app.utils.helpers import get_account_service

router = APIRouter(prefix='/accounts', tags=['Accounts'])


@router.get("/accounts", response_model=List[Account])
async def get_accounts(
    name_prefix: str = None,
    account_service: AccountService = Depends(get_account_service)
):
    """Get accounts with optional name prefix filter"""
    try:
        accounts = account_service.get_accounts_with_sync(name_prefix)
        return [Account.model_validate(account) for account in accounts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
