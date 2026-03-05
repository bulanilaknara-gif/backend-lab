import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")

AUTH_DB = {
    "host": os.getenv("AUTH_DB_HOST"),
    "port": os.getenv("AUTH_DB_PORT"),
    "dbname": os.getenv("AUTH_DB_NAME"),
    "user": os.getenv("AUTH_DB_USER"),
    "password": os.getenv("AUTH_DB_PASSWORD"),
}

HOSPITAL_DB = {
    "host": os.getenv("HOSPITAL_DB_HOST"),
    "port": os.getenv("HOSPITAL_DB_PORT"),
    "dbname": os.getenv("HOSPITAL_DB_NAME"),
    "user": os.getenv("HOSPITAL_DB_USER"),
    "password": os.getenv("HOSPITAL_DB_PASSWORD"),
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH") or os.path.join(BASE_DIR, "firebase_service_key.json")