from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
from fastapi import HTTPException

from services.auth import AuthService
from models.auth import Token
from tests.base import BaseTestCase


class TestAuthService(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.auth_service = AuthService(self.db_session)
        self.mock_token_data = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'realm_id': 'test_realm_id',
            'expires_in': 3600
        }

    @patch('services.auth.AuthClient')
    def test_auth_client_property(self, mock_auth_client_class):
        """Test auth_client property creates and returns an AuthClient instance"""
        # Mock the AuthClient class
        mock_auth_client = MagicMock()
        mock_auth_client_class.return_value = mock_auth_client
        
        # Get the auth_client property
        auth_client = self.auth_service.auth_client
        
        # Verify AuthClient was created with correct parameters
        mock_auth_client_class.assert_called_once()
        self.assertEqual(auth_client, mock_auth_client)
        
        # Get it again to verify caching
        auth_client2 = self.auth_service.auth_client
        # The mock is called twice - once for each access to the property
        self.assertEqual(mock_auth_client_class.call_count, 2)
        self.assertEqual(auth_client2, mock_auth_client)

    def test_save_token_new_token(self):
        """Test save_token when no token exists"""
        # Save a new token
        token = self.auth_service.save_token(
            access_token=self.mock_token_data['access_token'],
            refresh_token=self.mock_token_data['refresh_token'],
            realm_id=self.mock_token_data['realm_id'],
            expires_in=self.mock_token_data['expires_in']
        )
        
        # Verify token was saved
        self.assertIsNotNone(token)
        self.assertEqual(token.access_token, self.mock_token_data['access_token'])
        self.assertEqual(token.refresh_token, self.mock_token_data['refresh_token'])
        self.assertEqual(token.realm_id, self.mock_token_data['realm_id'])
        self.assertIsNotNone(token.expires_at)
        
        # Verify token is in database
        db_token = self.db_session.query(Token).first()
        self.assertIsNotNone(db_token)
        self.assertEqual(db_token.access_token, self.mock_token_data['access_token'])

    def test_save_token_update_existing(self):
        """Test save_token when a token already exists"""
        # Create an existing token
        existing_token = Token(
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            realm_id='old_realm_id',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.db_session.add(existing_token)
        self.db_session.commit()
        
        # Save a new token
        token = self.auth_service.save_token(
            access_token=self.mock_token_data['access_token'],
            refresh_token=self.mock_token_data['refresh_token'],
            realm_id=self.mock_token_data['realm_id'],
            expires_in=self.mock_token_data['expires_in']
        )
        
        # Verify token was updated
        self.assertIsNotNone(token)
        self.assertEqual(token.access_token, self.mock_token_data['access_token'])
        self.assertEqual(token.refresh_token, self.mock_token_data['refresh_token'])
        self.assertEqual(token.realm_id, self.mock_token_data['realm_id'])
        
        # Verify only one token exists in database
        db_tokens = self.db_session.query(Token).all()
        self.assertEqual(len(db_tokens), 1)
        self.assertEqual(db_tokens[0].access_token, self.mock_token_data['access_token'])

    def test_get_valid_token_no_token(self):
        """Test get_valid_token when no token exists"""
        # Verify exception is raised
        with self.assertRaises(HTTPException) as context:
            self.auth_service.get_valid_token()
        
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("No token found", str(context.exception.detail))

    def test_get_valid_token_valid_token(self):
        """Test get_valid_token when token is valid"""
        # Create a valid token
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = Token(
            access_token=self.mock_token_data['access_token'],
            refresh_token=self.mock_token_data['refresh_token'],
            realm_id=self.mock_token_data['realm_id'],
            expires_at=expires_at
        )
        self.db_session.add(token)
        self.db_session.commit()
        
        # Get the token
        valid_token = self.auth_service.get_valid_token()
        
        # Verify token was returned
        self.assertIsNotNone(valid_token)
        self.assertEqual(valid_token.access_token, self.mock_token_data['access_token'])

    @patch('services.auth.requests.post')
    def test_refresh_token(self, mock_post):
        """Test refresh_token method"""
        # Create an existing token
        expires_at = datetime.utcnow() - timedelta(minutes=10)  # Expired token
        token = Token(
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            realm_id='test_realm_id',
            expires_at=expires_at
        )
        self.db_session.add(token)
        self.db_session.commit()
        
        # Mock the refresh token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        # Refresh the token
        refreshed_token = self.auth_service.refresh_token(token)
        
        # Verify token was refreshed
        self.assertIsNotNone(refreshed_token)
        self.assertEqual(refreshed_token.access_token, 'new_access_token')
        self.assertEqual(refreshed_token.refresh_token, 'new_refresh_token')
        self.assertEqual(refreshed_token.realm_id, 'test_realm_id')
        
        # Verify API call
        mock_post.assert_called_once()
        # Check that the data dictionary contains the expected keys
        self.assertEqual(mock_post.call_args[1]['data']['grant_type'], 'refresh_token')
        self.assertEqual(mock_post.call_args[1]['data']['refresh_token'], 'old_refresh_token')

    @patch('services.auth.requests.post')
    def test_refresh_token_error(self, mock_post):
        """Test refresh_token method with API error"""
        # Create an existing token
        expires_at = datetime.utcnow() - timedelta(minutes=10)  # Expired token
        token = Token(
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            realm_id='test_realm_id',
            expires_at=expires_at
        )
        self.db_session.add(token)
        self.db_session.commit()
        
        # Mock the refresh token error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid refresh token"
        mock_post.return_value = mock_response
        
        # Verify exception is raised
        with self.assertRaises(HTTPException) as context:
            self.auth_service.refresh_token(token)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Failed to refresh token", str(context.exception.detail))

    def test_get_valid_token_expired_token(self):
        """Test get_valid_token when token is expired"""
        # Create an expired token
        expires_at = datetime.utcnow() - timedelta(minutes=10)  # Expired token
        token = Token(
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            realm_id='test_realm_id',
            expires_at=expires_at
        )
        self.db_session.add(token)
        self.db_session.commit()
        
        # Mock the refresh_token method
        with patch.object(AuthService, 'refresh_token') as mock_refresh:
            mock_refresh.return_value = Token(
                access_token='new_access_token',
                refresh_token='new_refresh_token',
                realm_id='test_realm_id',
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            # Get the token
            valid_token = self.auth_service.get_valid_token()
            
            # Verify refresh_token was called
            mock_refresh.assert_called_once_with(token)
            
            # Verify new token was returned
            self.assertIsNotNone(valid_token)
            self.assertEqual(valid_token.access_token, 'new_access_token')
