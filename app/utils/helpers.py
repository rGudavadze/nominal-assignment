from fastapi import Depends

from sqlalchemy.orm import Session

from services.account import AccountService
from services.auth import AuthService
from database import get_db


def get_auth_service(db: Session = Depends(get_db)):
    return AuthService(db)


def get_account_service(
    db: Session = Depends(get_db),
    token_service: AuthService = Depends(get_auth_service)
):
    return AccountService(db, token_service)
