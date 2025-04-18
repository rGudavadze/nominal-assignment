from typing import List

from fastapi import Depends, APIRouter

from schemas.account import AccountSchema
from services.account import AccountService
from utils.helpers import get_account_service

router = APIRouter(prefix='/accounts', tags=['Accounts'])


@router.get("", response_model=List[AccountSchema])
async def get_accounts(
    name_prefix: str = None,
    from_api: str = None,
    account_service: AccountService = Depends(get_account_service),
    response_model=List[AccountSchema]
):
    """Get accounts with optional name prefix filter"""
    accounts = account_service.get_accounts_with_sync(name_prefix, from_api)
    return accounts
