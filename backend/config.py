import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///projectpeak.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))

    JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "120"))
    COOKIE_NAME = os.getenv("COOKIE_NAME", "pp_access")
