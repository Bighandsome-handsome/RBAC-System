# tests/test_auth.py

def test_register_page_loads(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/register' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/register')
    assert response.status_code == 200
    assert b"Join Today" in response.data

def test_login_page_loads(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b"Log In" in response.data

def test_successful_registration_and_login(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN a new user is registered (POST) and then logs in (POST)
    THEN check that the registration is successful and the login redirects to the dashboard
    """
    # Register a new user
    response_register = test_client.post('/register',
                                         data={'username': 'testuser',
                                               'email': 'test@example.com',
                                               'password': 'password123',
                                               'confirm_password': 'password123'},
                                         follow_redirects=True)
    assert response_register.status_code == 200
    assert b"Your account has been created!" in response_register.data

    # Log in with the new user
    response_login = test_client.post('/login',
                                      data={'email': 'test@example.com',
                                            'password': 'password123'},
                                      follow_redirects=True)
    assert response_login.status_code == 200
    assert b"Welcome to your Dashboard" in response_login.data

def test_dashboard_access_without_login(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/dashboard' page is requested without logging in
    THEN check that the user is redirected to the login page
    """
    response = test_client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b"Log In" in response.data # Should be on the login page