from fastapi import Depends

from sqlalchemy.orm import Session

from app.services.account import AccountService
from app.services.auth import AuthService
from app.database import get_db


def get_token_service(db: Session = Depends(get_db)):
    return AuthService(db)


def get_account_service(
    db: Session = Depends(get_db),
    token_service: AuthService = Depends(get_token_service)
):
    return AccountService(db, token_service)
