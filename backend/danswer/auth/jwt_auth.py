import os

from fastapi_users.authentication import JWTAuthentication

# JWT settings
SECRET = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

jwt_authentication = JWTAuthentication(
    secret=SECRET, lifetime_seconds=60 * ACCESS_TOKEN_EXPIRE_MINUTES, tokenUrl="auth/jwt/login", algorithm=ALGORITHM
)