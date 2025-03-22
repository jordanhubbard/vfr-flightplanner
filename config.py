class Config:
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable caching for static files
    
class DevelopmentConfig(Config):
    FLASK_ENV = 'development'
    # Add any additional development-specific settings here 