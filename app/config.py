import os

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable caching for static files
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
