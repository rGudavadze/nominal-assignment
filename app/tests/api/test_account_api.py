from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from tests.base import BaseTestCase
from models.account import Account
from main import app


class TestAccountAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = TestClient(app)

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    @patch('services.account.AccountService.get_accounts_with_sync')
    def test_get_accounts_no_filter(self, mock_get_accounts):
        """Test get accounts endpoint without name prefix filter"""
        # Create test accounts
        accounts = [
            Account(
                id=1,
                qbo_id="1",
                name="Test Account 1",
                classification="Asset",
                account_type="Bank",
                active=True,
                current_balance=1000.0
            ),
            Account(
                id=2,
                qbo_id="2",
                name="Test Account 2",
                classification="Liability",
                account_type="Credit Card",
                active=True,
                current_balance=-500.0
            )
        ]
        mock_get_accounts.return_value = accounts

        # Make request
        response = self.client.get("/accounts")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Test Account 1")
        self.assertEqual(data[1]["name"], "Test Account 2")
        mock_get_accounts.assert_called_once_with(None, None)

    @patch('services.account.AccountService.get_accounts_with_sync')
    def test_get_accounts_with_filter(self, mock_get_accounts):
        """Test get accounts endpoint with name prefix filter"""
        # Create test accounts
        accounts = [
            Account(
                id=1,
                qbo_id="1",
                name="Asset Account",
                classification="Asset",
                account_type="Bank",
                active=True,
                current_balance=1000.0
            )
        ]
        mock_get_accounts.return_value = accounts

        # Make request with name prefix
        response = self.client.get("/accounts?name_prefix=Asset")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Asset Account")
        mock_get_accounts.assert_called_once_with("Asset", None)

    @patch('services.account.AccountService.get_accounts_with_sync')
    def test_get_accounts_empty_response(self, mock_get_accounts):
        """Test get accounts endpoint when no accounts are found"""
        mock_get_accounts.return_value = []

        # Make request
        response = self.client.get("/accounts")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 0)
        mock_get_accounts.assert_called_once_with(None, None)

    @patch('services.account.AccountService.get_accounts_with_sync')
    def test_get_accounts_error(self, mock_get_accounts):
        """Test get accounts endpoint when service raises an error"""
        mock_get_accounts.side_effect = HTTPException(400, "Failed to fetch accounts")

        # Make request
        response = self.client.get("/accounts")
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to fetch accounts", response.json()["detail"])

    @patch('services.account.AccountService.get_accounts_with_sync')
    def test_get_accounts_sync_error(self, mock_get_accounts):
        """Test get accounts endpoint when sync fails"""
        mock_get_accounts.side_effect = HTTPException(500, "Sync failed")

        # Make request
        response = self.client.get("/accounts")
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        self.assertIn("Sync failed", response.json()["detail"]) 