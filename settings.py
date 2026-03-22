import os

from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = "repgen_images"
DOCUMENTS_BUCKET_NAME = os.environ.get("DOCUMENTS_BUCKET_NAME", "repgen_documents")
PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = os.environ.get("LOCATION", "global")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SQL_USER = os.environ.get("SQL_USER", "postgres")
SQL_PASSWORD = os.environ.get("SQL_PASSWORD", "password")
SQL_DB = os.environ.get("SQL_DB", "repgen_db")
SQL_HOST = os.environ.get("SQL_HOST", "db")
SQL_PORT = os.environ.get("SQL_PORT", "5432")
PATH_PG_DATA = os.environ.get("PATH_PG_DATA", "./postgres_data")

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")

# Focus API configuration
FOCUS_API_URL = os.environ.get("FOCUS_API_URL")
FOCUS_API_KEY = os.environ.get("FOCUS_API_KEY")
FOCUS_API_SECRET = os.environ.get("FOCUS_API_SECRET")

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 60  # 60 дней

# Construction queue settings
CONSTRUCTION_QUEUE_MAX_CONCURRENT = 5
CONSTRUCTION_QUEUE_MAX_SIZE = 500

# Defect analysis queue settings
DEFECT_QUEUE_MAX_CONCURRENT = 3
DEFECT_QUEUE_MAX_SIZE = 200
