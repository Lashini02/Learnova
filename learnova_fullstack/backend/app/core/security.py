from datetime import datetime, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_bytes
from typing import Optional
import base64

from jose import jwt, JWTError
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DELTA

HASH_ITERATIONS = 100_000
SALT_SIZE = 16

def hash_password(password: str) -> str:
    salt = token_bytes(SALT_SIZE)
    key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ITERATIONS)
    return base64.b64encode(salt + key).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        decoded = base64.b64decode(hashed_password.encode("utf-8"))
        salt = decoded[:SALT_SIZE]
        stored_key = decoded[SALT_SIZE:]
        key = pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, HASH_ITERATIONS)
        return compare_digest(stored_key, key)
    except (TypeError, ValueError):
        return False


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE_DELTA
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
