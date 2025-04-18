from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session
import requests
from typing import List, Optional, Dict, Any

from models.account import Account
from models.sync import SyncLog
from config.settings import settings
from services.auth import AuthService
from schemas.account import AccountCreateSchema


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
    
    def _fetch_accounts_from_api(self, last_sync_time: Optional[datetime]) -> List[Dict[str, Any]]:
        """Fetch accounts from QuickBooks API that have been updated since last_sync_time."""
        token = self.auth_service.get_valid_token()

        url = f"{settings.API_BASE}/company/{token.realm_id}/query"
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/text"
        }
        # Query for accounts updated since the last sync
        query = (
            f"SELECT * FROM Account WHERE Metadata.LastUpdatedTime >= '{last_sync_time}'"
            if last_sync_time
            else "SELECT * FROM Account"
        )
        
        response = requests.post(url, data=query, headers=headers)
        if response.status_code != 200:
            raise HTTPException(400, f"Failed to fetch accounts: {response.text}")

        return response.json().get('QueryResponse', {}).get('Account', [])

    def _get_existing_accounts(self, account_ids: List[str]) -> Dict[str, Account]:
        """Get existing accounts by qbo_id for efficient lookup"""
        accounts = {
            account.qbo_id: account 
            for account in self.db.query(Account).filter(
                Account.qbo_id.in_(account_ids)
            ).all()
        }
        return accounts

    @staticmethod
    def _validate_account(account_data: Dict[str, Any]) -> AccountCreateSchema:
        """Create an AccountCreateSchema object from API data"""
        return AccountCreateSchema(
            qbo_id=account_data['Id'],
            name=account_data['Name'],
            classification=account_data.get('Classification'),
            currency_ref=account_data.get('CurrencyRef', {}).get('value'),
            account_type=account_data.get('AccountType'),
            active=account_data.get('Active', True),
            current_balance=account_data.get('CurrentBalance', 0.0),
            parent_id=account_data.get('ParentRef', {}).get('value')
        )

    @staticmethod
    def _update_account_instance(account: Account, account_create: AccountCreateSchema) -> Account:
        """Update an existing account with new data"""
        account.name = account_create.name
        account.classification = account_create.classification
        account.currency_ref = account_create.currency_ref
        account.account_type = account_create.account_type
        account.active = account_create.active
        account.current_balance = account_create.current_balance
        account.parent_id = account_create.parent_id
        return account

    @staticmethod
    def _create_account_instance(account_create: AccountCreateSchema) -> Account:
        """Create a new account from AccountCreateSchema data"""
        return Account(
            qbo_id=account_create.qbo_id,
            name=account_create.name,
            classification=account_create.classification,
            currency_ref=account_create.currency_ref,
            account_type=account_create.account_type,
            active=account_create.active,
            current_balance=account_create.current_balance,
            parent_id=account_create.parent_id
        )
    
    def _process_accounts(self, accounts_data: List[Dict[str, Any]]) -> tuple[List[Account], List[Account]]:
        """Process accounts data and return lists of accounts to update and create"""
        account_ids = [acc['Id'] for acc in accounts_data]
        existing_accounts = self._get_existing_accounts(account_ids)
        
        accounts_to_update = []
        accounts_to_create = []
        
        for account_data in accounts_data:
            qbo_id = account_data['Id']
            account_create = self._validate_account(account_data)
            
            if qbo_id in existing_accounts:
                # Update existing account
                account = existing_accounts[qbo_id]
                updated_account = self._update_account_instance(account, account_create)
                accounts_to_update.append(updated_account)
            else:
                # Create new account
                new_account = self._create_account_instance(account_create)
                accounts_to_create.append(new_account)
        
        return accounts_to_update, accounts_to_create
    
    def _save_accounts_to_db(self, accounts_to_update: List[Account], accounts_to_create: List[Account]):
        """Save accounts to database using bulk operations"""
        if accounts_to_create:
            self.db.bulk_save_objects(accounts_to_create)
        for account in accounts_to_update:
            self.db.merge(account)
        
        self.db.commit()
    
    def sync_accounts(self):
        """Sync accounts from QuickBooks to database using bulk operations"""
        print("Syncing accounts...")
        last_sync_time = self.last_sync_time
        if last_sync_time:
            last_sync_time = last_sync_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        accounts_data = self._fetch_accounts_from_api(last_sync_time)
        
        if not accounts_data:
            print(f"No accounts updated since {last_sync_time}")
            self.update_last_sync_time(datetime.utcnow())
            return
        
        accounts_to_update, accounts_to_create = self._process_accounts(accounts_data)
        self._save_accounts_to_db(accounts_to_update, accounts_to_create)
        
        self.update_last_sync_time(datetime.utcnow())
    
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
    
    def get_accounts_with_sync(self, name_prefix: Optional[str] = None, from_api=False) -> List[Account]:
        """Get accounts, syncing first if necessary"""
        if from_api or self.should_sync():
            self.sync_accounts()
        
        return self.get_accounts(name_prefix)
