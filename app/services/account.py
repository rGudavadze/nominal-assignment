from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session
import requests
from typing import List, Optional, Dict, Any

from models.account import Account
from models.sync import SyncLog
from config.settings import settings
from services.auth import AuthService
from schemas.account import AccountCreate


class AccountService:
    def __init__(self, db: Session, auth_service: AuthService):
        self.db = db
        self.auth_service = auth_service

    @property
    def last_sync_time(self) -> Optional[datetime]:
        """Get the last sync time for accounts from the sync_logs table"""
        sync_log = self.db.query(SyncLog).filter_by(entity_type='account').first()
        if not sync_log:
            return None
        return sync_log.last_sync_at
    
    def update_last_sync_time(self, sync_time: datetime):
        """Update the last sync time in the sync_logs table"""
        sync_log = self.db.query(SyncLog).filter_by(entity_type='account').first()
        if not sync_log:
            sync_log = SyncLog(entity_type='account')
            self.db.add(sync_log)
        
        sync_log.last_sync_at = sync_time
        self.db.commit()
    
    def sync_accounts(self):
        """Sync accounts from QuickBooks to database using bulk operations"""
        token = self.auth_service.get_valid_token()

        url = f"{settings.API_BASE}/company/{token.realm_id}/query"
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/text"
        }
        
        last_sync_time = self.last_sync_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Query for accounts updated since the last sync
        query = f"SELECT * FROM Account WHERE Metadata.LastUpdatedTime >= '{last_sync_time}'"
        
        response = requests.post(url, data=query, headers=headers)
        if response.status_code != 200:
            raise HTTPException(400, f"Failed to fetch accounts: {response.text}")

        current_sync_time = datetime.utcnow()
        accounts_data = response.json().get('QueryResponse', {}).get('Account', [])

        # Only update the sync time if we actually found and processed accounts
        if not accounts_data:
            print(f"No accounts updated since {last_sync_time}")
            self.update_last_sync_time(current_sync_time)
            return

        # Get all existing accounts by qbo_id for efficient lookup
        existing_accounts = {
            account.qbo_id: account 
            for account in self.db.query(Account).filter(
                Account.qbo_id.in_([acc['Id'] for acc in accounts_data])
            ).all()
        }
        
        # Prepare lists for bulk operations
        accounts_to_update = []
        accounts_to_create = []
        
        for account_data in accounts_data:
            qbo_id = account_data['Id']
            
            account_create = AccountCreate(
                qbo_id=qbo_id,
                name=account_data['Name'],
                classification=account_data.get('Classification'),
                currency_ref=account_data.get('CurrencyRef', {}).get('value'),
                account_type=account_data.get('AccountType'),
                active=account_data.get('Active', True),
                current_balance=account_data.get('CurrentBalance', 0.0),
                parent_id=account_data.get('ParentRef', {}).get('value')
            )
            
            if qbo_id in existing_accounts:
                # Update existing account
                account = existing_accounts[qbo_id]
                account.name = account_create.name
                account.classification = account_create.classification
                account.currency_ref = account_create.currency_ref
                account.account_type = account_create.account_type
                account.active = account_create.active
                account.current_balance = account_create.current_balance
                account.parent_id = account_create.parent_id
                accounts_to_update.append(account)
            else:
                # Create new account
                account = Account(
                    qbo_id=account_create.qbo_id,
                    name=account_create.name,
                    classification=account_create.classification,
                    currency_ref=account_create.currency_ref,
                    account_type=account_create.account_type,
                    active=account_create.active,
                    current_balance=account_create.current_balance,
                    parent_id=account_create.parent_id
                )
                accounts_to_create.append(account)
        
        # Perform bulk operations
        if accounts_to_create:
            self.db.bulk_save_objects(accounts_to_create)
        
        # Bulk update is not directly supported by SQLAlchemy, so we need to use a session
        for account in accounts_to_update:
            self.db.merge(account)
        
        # Commit all changes at once
        self.db.commit()
        
        # Update the sync time
        self.update_last_sync_time(current_sync_time)
    
    def get_accounts(self, name_prefix: Optional[str] = None) -> List[Account]:
        """Get accounts with optional name prefix filter"""
        query = self.db.query(Account)
        
        if name_prefix:
            query = query.filter(Account.name.ilike(f"{name_prefix}%"))
        
        return query.all()
    
    def should_sync(self) -> bool:
        """Check if accounts need to be synced (older than 1 hour)"""
        print("Checking if accounts need to be synced...")
        last_sync = self.last_sync_time
        if not last_sync:
            return True
        
        return datetime.utcnow() - last_sync > timedelta(hours=1)
    
    def get_accounts_with_sync(self, name_prefix: Optional[str] = None) -> List[Account]:
        """Get accounts, syncing first if necessary"""
        if self.should_sync():
            self.sync_accounts()
        
        return self.get_accounts(name_prefix)
