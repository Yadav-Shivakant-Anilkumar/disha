import os

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'disha-computer-secret-key-2026'
    DEBUG = True
    
    # Database settings for MySQL (XAMPP)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # XAMPP default has no password
    DB_NAME = os.environ.get('DB_NAME', 'disha_computer')
    DB_PORT = int(os.environ.get('DB_PORT', '3309'))
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'mp4'}
    
    # Session settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Pagination
    ITEMS_PER_PAGE = 10
    
    @staticmethod
    def init_app(app):
        """Initialize application"""
        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'materials'), exist_ok=True)
        os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'certificates'), exist_ok=True)
        os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'photos'), exist_ok=True)
