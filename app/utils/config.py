import os
from dotenv import load_dotenv

load_dotenv()


env = os.getenv("ENV")
port = os.getenv("PORT")
SHARED_SECRET = os.getenv("INTERNAL_SECRET_TOKEN", "fallback-secret-for-dev")
database_url = os.getenv("DATABASE_URL", "postgresql://dummy:dummy@localhost/dummy")
mp_token = os.getenv("MP_ACCESS_TOKEN_TEST")
if not mp_token:
    raise ValueError("Falta configurar MP_ACCESS_TOKEN_TEST en el .env")

ms_club_url = os.getenv("MS_CLUB_URL", "http://localhost:8000")  # URL del microservicio ms-club
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # URL de Redis