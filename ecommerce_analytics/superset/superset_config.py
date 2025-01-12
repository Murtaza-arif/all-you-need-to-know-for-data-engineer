from flask_appbuilder.security.manager import AUTH_DB

# Superset specific config
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

# Flask App Builder configuration
APP_NAME = "E-commerce Analytics"
SECRET_KEY = 'your_secret_key_here'

# Allow SQLite database
PREVENT_UNSAFE_DB_CONNECTIONS = False
SQLALCHEMY_ALLOW_UNSAFE_DIALECTS = True

# Authentication config
AUTH_TYPE = AUTH_DB
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public"

# Enable file upload
ENABLE_PROXY_FIX = True
UPLOAD_FOLDER = '/app/superset_home/uploads/'
IMG_UPLOAD_FOLDER = '/app/superset_home/uploads/'

# Cache config
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
}
