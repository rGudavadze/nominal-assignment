from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
from fastapi import HTTPException

from services.account import AccountService
from models.account import Account
from models.sync import SyncLog
from tests.base import BaseTestCase


class TestAccountService(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account_service = AccountService(self.db_session, self.mock_auth_service)
        self.mock_account_data = [
            {
                "Id": "1",
                "Name": "Test Account 1",
                "Classification": "Asset",
                "CurrencyRef": {"value": "USD"},
                "AccountType": "Bank",
                "Active": True,
                "CurrentBalance": 1000.0,
                "ParentRef": {"value": None}
            },
            {
                "Id": "2",
                "Name": "Test Account 2",
                "Classification": "Liability",
                "CurrencyRef": {"value": "USD"},
                "AccountType": "Credit Card",
                "Active": True,
                "CurrentBalance": -500.0,
                "ParentRef": {"value": None}
            }
        ]

    def test_last_sync_time_no_sync_log(self):
        """Test last_sync_time when no sync log exists"""
        self.assertIsNone(self.account_service.last_sync_time)

    def test_last_sync_time_with_sync_log(self):
        """Test last_sync_time when sync log exists"""
        sync_log = self.create_sync_log()
        self.assertIsNotNone(self.account_service.last_sync_time)
        self.assertIsInstance(self.account_service.last_sync_time, datetime)

    def test_update_last_sync_time_new_log(self):
        """Test update_last_sync_time when no sync log exists"""
        sync_time = datetime.utcnow()
        self.account_service.update_last_sync_time(sync_time)
        
        sync_log = self.db_session.query(SyncLog).filter_by(entity_type='account').first()
        self.assertIsNotNone(sync_log)
        self.assertEqual(sync_log.last_sync_at, sync_time)

    def test_update_last_sync_time_existing_log(self):
        """Test update_last_sync_time when sync log exists"""
        sync_log = self.create_sync_log()
        old_sync_time = sync_log.last_sync_at
        new_sync_time = datetime.utcnow()
        
        self.account_service.update_last_sync_time(new_sync_time)
        
        sync_log = self.db_session.query(SyncLog).filter_by(entity_type='account').first()
        self.assertEqual(sync_log.last_sync_at, new_sync_time)
        self.assertNotEqual(sync_log.last_sync_at, old_sync_time)

    @patch('services.account.requests.post')
    def test_fetch_accounts_from_api(self, mock_post):
        """Test _fetch_accounts_from_api method"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'QueryResponse': {
                'Account': [
                    {'Id': '1', 'Name': 'Test Account'}
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # Test with last_sync_time
        last_sync_time = datetime.utcnow() - timedelta(hours=1)
        accounts = self.account_service._fetch_accounts_from_api(last_sync_time)
        
        # Verify API call
        mock_post.assert_called_once()
        self.assertIn('Authorization', mock_post.call_args[1]['headers'])
        self.assertIn('Bearer test_access_token', mock_post.call_args[1]['headers']['Authorization'])
        
        # Verify returned data
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]['Id'], '1')
        self.assertEqual(accounts[0]['Name'], 'Test Account')

    @patch('services.account.requests.post')
    def test_fetch_accounts_from_api_error(self, mock_post):
        """Test _fetch_accounts_from_api method with API error"""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        # Test with last_sync_time
        last_sync_time = datetime.utcnow() - timedelta(hours=1)
        
        # Verify exception is raised
        with self.assertRaises(HTTPException) as context:
            self.account_service._fetch_accounts_from_api(last_sync_time)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Failed to fetch accounts", str(context.exception.detail))

    def test_get_existing_accounts(self):
        """Test _get_existing_accounts method"""
        # Create test accounts
        account1 = self.create_test_account(qbo_id="1", name="Test Account 1")
        account2 = self.create_test_account(qbo_id="2", name="Test Account 2")
        
        # Test getting existing accounts
        account_ids = ["1", "2", "3"]  # "3" doesn't exist
        existing_accounts = self.account_service._get_existing_accounts(account_ids)
        
        # Verify results
        self.assertEqual(len(existing_accounts), 2)
        self.assertIn("1", existing_accounts)
        self.assertIn("2", existing_accounts)
        self.assertNotIn("3", existing_accounts)
        self.assertEqual(existing_accounts["1"].name, "Test Account 1")
        self.assertEqual(existing_accounts["2"].name, "Test Account 2")

    def test_validate_account(self):
        """Test _validate_account method"""
        # Test data
        account_data = {
            'Id': '1',
            'Name': 'Test Account',
            'Classification': 'Asset',
            'CurrencyRef': {'value': 'USD'},
            'AccountType': 'Bank',
            'Active': True,
            'CurrentBalance': 1000.0,
            'ParentRef': {'value': '2'}
        }
        
        # Create account from data
        account_create = self.account_service._validate_account(account_data)
        
        # Verify account data
        self.assertEqual(account_create.qbo_id, '1')
        self.assertEqual(account_create.name, 'Test Account')
        self.assertEqual(account_create.classification, 'Asset')
        self.assertEqual(account_create.currency_ref, 'USD')
        self.assertEqual(account_create.account_type, 'Bank')
        self.assertTrue(account_create.active)
        self.assertEqual(account_create.current_balance, 1000.0)
        self.assertEqual(account_create.parent_id, '2')

    def test_update_account_instance(self):
        """Test _update_account_instance method"""
        # Create test account
        account = Account(
            qbo_id="1",
            name="Old Name",
            classification="Old Classification",
            currency_ref="EUR",
            account_type="Old Type",
            active=False,
            current_balance=0.0,
            parent_id=None
        )
        
        # Create account data
        from schemas.account import AccountCreateSchema
        account_create = AccountCreateSchema(
            qbo_id="1",
            name="New Name",
            classification="New Classification",
            currency_ref="USD",
            account_type="New Type",
            active=True,
            current_balance=1000.0,
            parent_id="2"
        )
        
        # Update account
        updated_account = self.account_service._update_account_instance(account, account_create)
        
        # Verify updated account
        self.assertEqual(updated_account.qbo_id, '1')  # Should not change
        self.assertEqual(updated_account.name, 'New Name')
        self.assertEqual(updated_account.classification, 'New Classification')
        self.assertEqual(updated_account.currency_ref, 'USD')
        self.assertEqual(updated_account.account_type, 'New Type')
        self.assertTrue(updated_account.active)
        self.assertEqual(updated_account.current_balance, 1000.0)
        self.assertEqual(updated_account.parent_id, '2')

    def test_create_account_instance(self):
        """Test _create_account_instance method"""
        # Create account data
        from schemas.account import AccountCreateSchema
        account_create = AccountCreateSchema(
            qbo_id="1",
            name="Test Account",
            classification="Asset",
            currency_ref="USD",
            account_type="Bank",
            active=True,
            current_balance=1000.0,
            parent_id="2"
        )
        
        # Create new account
        new_account = self.account_service._create_account_instance(account_create)
        
        # Verify new account
        self.assertEqual(new_account.qbo_id, '1')
        self.assertEqual(new_account.name, 'Test Account')
        self.assertEqual(new_account.classification, 'Asset')
        self.assertEqual(new_account.currency_ref, 'USD')
        self.assertEqual(new_account.account_type, 'Bank')
        self.assertTrue(new_account.active)
        self.assertEqual(new_account.current_balance, 1000.0)
        self.assertEqual(new_account.parent_id, '2')

    @patch('services.account.AccountService._get_existing_accounts')
    def test_process_accounts(self, mock_get_existing_accounts):
        """Test _process_accounts method"""
        # Mock existing accounts
        mock_get_existing_accounts.return_value = {
            "1": Account(qbo_id="1", name="Existing Account 1")
        }
        
        # Process accounts
        accounts_to_update, accounts_to_create = self.account_service._process_accounts(self.mock_account_data)
        
        # Verify results
        self.assertEqual(len(accounts_to_update), 1)
        self.assertEqual(len(accounts_to_create), 1)
        
        # Verify updated account
        self.assertEqual(accounts_to_update[0].qbo_id, "1")
        self.assertEqual(accounts_to_update[0].name, "Test Account 1")
        
        # Verify created account
        self.assertEqual(accounts_to_create[0].qbo_id, "2")
        self.assertEqual(accounts_to_create[0].name, "Test Account 2")

    def test_save_accounts_to_db(self):
        """Test _save_accounts_to_db method"""
        # Create test accounts
        account_to_update = self.create_test_account(qbo_id="1", name="Account to Update")
        account_to_create = Account(qbo_id="2", name="Account to Create")
        
        # Save accounts to database
        self.account_service._save_accounts_to_db([account_to_update], [account_to_create])
        
        # Verify accounts in database
        updated_account = self.db_session.query(Account).filter_by(qbo_id="1").first()
        created_account = self.db_session.query(Account).filter_by(qbo_id="2").first()
        
        self.assertIsNotNone(updated_account)
        self.assertIsNotNone(created_account)
        self.assertEqual(updated_account.name, "Account to Update")
        self.assertEqual(created_account.name, "Account to Create")

    @patch('services.account.AccountService._fetch_accounts_from_api')
    @patch('services.account.AccountService._process_accounts')
    @patch('services.account.AccountService._save_accounts_to_db')
    @patch('services.account.AccountService.update_last_sync_time')
    def test_sync_accounts_no_updates(
        self,
        mock_update_last_sync_time,
        mock_save_accounts_to_db,
        mock_process_accounts,
        mock_fetch_accounts_from_api
    ):
        """Test sync_accounts when no accounts need updating"""
        # Mock API response with no accounts
        mock_fetch_accounts_from_api.return_value = []
        
        # Call sync_accounts
        self.account_service.sync_accounts()
        
        # Verify methods were called
        mock_fetch_accounts_from_api.assert_called_once()
        mock_process_accounts.assert_not_called()
        mock_save_accounts_to_db.assert_not_called()
        mock_update_last_sync_time.assert_called_once()

    @patch('services.account.AccountService._fetch_accounts_from_api')
    @patch('services.account.AccountService._process_accounts')
    @patch('services.account.AccountService._save_accounts_to_db')
    @patch('services.account.AccountService.update_last_sync_time')
    def test_sync_accounts_with_updates(
        self,
        mock_update_last_sync_time,
        mock_save_accounts_to_db,
        mock_process_accounts,
        mock_fetch_accounts_from_api
    ):
        """Test sync_accounts when accounts need updating"""
        # Mock API response with accounts
        mock_fetch_accounts_from_api.return_value = self.mock_account_data
        
        # Mock process_accounts
        mock_process_accounts.return_value = ([], [])
        
        # Call sync_accounts
        self.account_service.sync_accounts()
        
        # Verify methods were called
        mock_fetch_accounts_from_api.assert_called_once()
        mock_process_accounts.assert_called_once_with(self.mock_account_data)
        mock_save_accounts_to_db.assert_called_once()
        mock_update_last_sync_time.assert_called_once()

    def test_get_accounts_no_filter(self):
        """Test get_accounts without name prefix filter"""
        # Create test accounts
        account1 = self.create_test_account(qbo_id="1", name="Test Account 1")
        account2 = self.create_test_account(qbo_id="2", name="Another Account")
        
        # Get accounts
        accounts = self.account_service.get_accounts()
        
        # Verify results
        self.assertEqual(len(accounts), 2)

    def test_get_accounts_with_filter(self):
        """Test get_accounts with name prefix filter"""
        # Create test accounts
        account1 = self.create_test_account(qbo_id="1", name="Test Account 1")
        account2 = self.create_test_account(qbo_id="2", name="Another Account")
        
        # Get accounts with filter
        accounts = self.account_service.get_accounts(name_prefix="Test")
        
        # Verify results
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].name, "Test Account 1")

    @patch('services.account.AccountService.last_sync_time', new_callable=PropertyMock)
    def test_should_sync_no_last_sync(self, mock_last_sync_time):
        """Test should_sync when no last sync time exists"""
        # Mock last_sync_time to return None
        mock_last_sync_time.return_value = None
        
        # Check if should sync
        self.assertTrue(self.account_service.should_sync())

    def test_should_sync_old_sync(self):
        """Test should_sync when last sync is old"""
        # Create sync log with old sync time
        self.create_sync_log(hours_ago=2)
        
        # Check if should sync
        self.assertTrue(self.account_service.should_sync())

    def test_should_sync_recent_sync(self):
        """Test should_sync when last sync is recent"""
        # Create sync log with recent sync time
        self.create_sync_log(hours_ago=0.5)  # 30 minutes ago
        
        # Check if should sync
        self.assertFalse(self.account_service.should_sync())

    @patch('services.account.AccountService.should_sync')
    @patch('services.account.AccountService.sync_accounts')
    def test_get_accounts_with_sync_needed(
        self,
        mock_sync_accounts,
        mock_should_sync
    ):
        """Test get_accounts_with_sync when sync is needed"""
        # Mock should_sync to return True
        mock_should_sync.return_value = True
        
        # Create test account
        account = self.create_test_account()
        
        # Get accounts with sync
        accounts = self.account_service.get_accounts_with_sync()
        
        # Verify methods were called
        mock_should_sync.assert_called_once()
        mock_sync_accounts.assert_called_once()
        
        # Verify results
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].name, "Test Account")

    @patch('services.account.AccountService.should_sync')
    @patch('services.account.AccountService.sync_accounts')
    def test_get_accounts_with_sync_not_needed(
        self,
        mock_sync_accounts,
        mock_should_sync
    ):
        """Test get_accounts_with_sync when sync is not needed"""
        # Mock should_sync to return False
        mock_should_sync.return_value = False
        
        # Create test account
        account = self.create_test_account()
        
        # Get accounts with sync
        accounts = self.account_service.get_accounts_with_sync()
        
        # Verify methods were called
        mock_should_sync.assert_called_once()
        mock_sync_accounts.assert_not_called()
        
        # Verify results
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].name, "Test Account")
