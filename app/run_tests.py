import os
import sys
import unittest
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database, drop_database

from config.test_settings import TestSettings
from database import Base


def setup_test_db():
    """Set up the test database"""
    settings = TestSettings()
    
    # Create test database if it doesn't exist
    if not database_exists(settings.TEST_DB_URL):
        create_database(settings.TEST_DB_URL)
    
    # Create all tables
    engine = create_engine(settings.TEST_DB_URL)
    Base.metadata.create_all(engine)
    engine.dispose()


def teardown_test_db():
    """Clean up the test database"""
    settings = TestSettings()
    if database_exists(settings.TEST_DB_URL):
        drop_database(settings.TEST_DB_URL)


def run_tests():
    """Run all tests"""
    # Set up test database
    setup_test_db()
    
    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = os.path.dirname(os.path.abspath(__file__))
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Return 0 if tests passed, 1 if any failed
        return 0 if result.wasSuccessful() else 1
    
    finally:
        # Clean up test database
        teardown_test_db()


if __name__ == '__main__':
    sys.exit(run_tests())
