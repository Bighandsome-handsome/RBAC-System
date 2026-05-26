# config.py

import os

# Get the absolute path of the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Base configuration class. Contains default configuration settings + configuration settings applicable to all environments.
    """
    # Default settings
    FLASK_ENV = 'development'
    DEBUG = False
    TESTING = False

    # Settings applicable to all environments
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key_for_development')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    """
    Configuration for testing.
    Uses an in-memory SQLite database.
    """
    TESTING = True
    # Use an in-memory SQLite database for tests
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Disable CSRF protection in forms for testing purposes
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:20041025@localhost:3306/flask_rbac_project?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False