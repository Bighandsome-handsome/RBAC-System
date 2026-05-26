# tests/conftest.py

import pytest
from app import create_app, db
from app.models import Role
from config import TestingConfig

# @pytest.fixture(scope='module')
@pytest.fixture
def test_client():
    """
    Creates a test client for the Flask application.
    This fixture is run once per test module.
    """
    # Create a Flask app configured for testing
    flask_app = create_app(config_class=TestingConfig)

    # Establish an application context
    with flask_app.app_context():
        # Create the database and the database tables
        db.create_all()

        # Create the roles to have them available for tests
        admin_role = Role(name='Admin')
        user_role = Role(name='User')
        db.session.add_all([admin_role, user_role])
        db.session.commit()
        
        # Create a test client using the Flask application configured for testing
        with flask_app.test_client() as testing_client:
            # Yield the test client to the tests
            yield testing_client
        
        # Teardown: drop all tables after the tests are done
        db.drop_all()