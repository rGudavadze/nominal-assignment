from typing import List

from fastapi import Depends, APIRouter

from schemas.account import Account
from services.account import AccountService
from utils.helpers import get_account_service

router = APIRouter(prefix='/accounts', tags=['Accounts'])


@router.get("", response_model=List[Account])
async def get_accounts(
    name_prefix: str = None,
    account_service: AccountService = Depends(get_account_service),
    response_model=List[Account]
):
    """Get accounts with optional name prefix filter"""
    accounts = account_service.get_accounts_with_sync(name_prefix)
    return accounts
