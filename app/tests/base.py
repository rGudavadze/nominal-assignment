import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base
from main import app
from services.auth import AuthService
from models.auth import Token
from models.sync import SyncLog
from config.test_settings import TestSettings
from utils.logger import logger


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test database and dependencies"""
        # Create test database
        self.settings = TestSettings()
        logger.info(f"Setting up test database: {self.settings.DB_NAME}")
        self.engine = create_engine(self.settings.TEST_DB_URL)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = self.SessionLocal()

        # Create mock auth service
        logger.debug("Setting up mock auth service")
        self.mock_auth_service = MagicMock(spec=AuthService)
        mock_token = MagicMock(spec=Token)
        mock_token.access_token = "test_access_token"
        mock_token.realm_id = "test_realm_id"
        self.mock_auth_service.get_valid_token.return_value = mock_token

        # Create test client
        logger.debug("Setting up test client")
        def override_get_db():
            try:
                yield self.db_session
            finally:
                pass

        def override_get_auth_service():
            return self.mock_auth_service

        app.dependency_overrides = {
            "get_db": override_get_db,
            "get_auth_service": override_get_auth_service
        }
        self.client = TestClient(app)

    def tearDown(self):
        """Clean up after tests"""
        logger.debug("Cleaning up test database")
        self.db_session.close()
        Base.metadata.drop_all(self.engine)
        app.dependency_overrides = {}

    def create_sync_log(self, hours_ago=2):
        """Helper method to create a sync log entry"""
        logger.debug(f"Creating sync log entry from {hours_ago} hours ago")
        sync_log = SyncLog(
            entity_type="account",
            last_sync_at=datetime.utcnow() - timedelta(hours=hours_ago)
        )
        self.db_session.add(sync_log)
        self.db_session.commit()
        return sync_log

    def create_test_account(self, qbo_id="1", name="Test Account"):
        """Helper method to create a test account"""
        logger.debug(f"Creating test account: {name} (ID: {qbo_id})")
        from models.account import Account
        account = Account(qbo_id=qbo_id, name=name)
        self.db_session.add(account)
        self.db_session.commit()
        return account
