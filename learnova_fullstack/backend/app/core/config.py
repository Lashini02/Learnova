import os
from datetime import timedelta

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./learnova.db")
SECRET_KEY = os.getenv("SECRET_KEY", "learnova-dev-secret-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
ACCESS_TOKEN_EXPIRE_DELTA = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
