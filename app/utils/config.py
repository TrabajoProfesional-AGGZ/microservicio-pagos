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