from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import requests
from typing import List, Optional

from models.account import Account
from config.settings import settings
from services.auth import AuthService
from schemas.account import AccountCreate


class AccountService:
    def __init__(self, db: Session, auth_service: AuthService):
        self.db = db
        self.auth_service = auth_service
    
    def sync_accounts(self):
        """Sync accounts from QuickBooks to local database"""
        token = self.auth_service.get_valid_token()
        
        url = f"{settings.API_BASE}/company/{token.realm_id}/query"
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/text"
        }
        query = "SELECT * FROM Account"
        
        response = requests.post(url, data=query, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch accounts: {response.text}")
        
        accounts_data = response.json().get('QueryResponse', {}).get('Account', [])
        
        for account_data in accounts_data:
            account = self.db.query(Account).filter_by(qbo_id=account_data['Id']).first()
            if not account:
                account = Account()
            
            # Create Pydantic model for validation
            account_create = AccountCreate(
                qbo_id=account_data['Id'],
                name=account_data['Name'],
                classification=account_data.get('Classification'),
                currency_ref=account_data.get('CurrencyRef', {}).get('value'),
                account_type=account_data.get('AccountType'),
                active=account_data.get('Active', True),
                current_balance=account_data.get('CurrentBalance', 0.0),
                parent_id=account_data.get('ParentRef', {}).get('value')
            )
            
            # Update account fields using validated data
            account.qbo_id = account_create.qbo_id
            account.name = account_create.name
            account.classification = account_create.classification
            account.currency_ref = account_create.currency_ref
            account.account_type = account_create.account_type
            account.active = account_create.active
            account.current_balance = account_create.current_balance
            account.parent_id = account_create.parent_id
            account.last_synced_at = datetime.utcnow()
            
            if not account.id:
                self.db.add(account)
        
        self.db.commit()
    
    def get_accounts(self, name_prefix: Optional[str] = None) -> List[Account]:
        """Get accounts with optional name prefix filter"""
        query = self.db.query(Account)
        
        if name_prefix:
            query = query.filter(Account.name.ilike(f"{name_prefix}%"))
        
        return query.all()
    
    def should_sync(self) -> bool:
        """Check if accounts need to be synced (older than 1 hour)"""
        print("Checking if accounts need to be synced...")
        last_sync = self.db.query(Account.last_synced_at).order_by(Account.last_synced_at.desc()).first()
        if not last_sync:
            return True
        
        return datetime.utcnow() - last_sync[0] > timedelta(hours=1)
    
    def get_accounts_with_sync(self, name_prefix: Optional[str] = None) -> List[Account]:
        """Get accounts, syncing first if necessary"""
        if self.should_sync():
            self.sync_accounts()
        
        return self.get_accounts(name_prefix)
