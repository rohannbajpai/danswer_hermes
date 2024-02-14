import os

from fastapi_users.authentication import JWTStrategy
from fastapi_users.authentication import AuthenticationBackend
from fastapi_users.authentication import BearerTransport

# JWT settings
SECRET = str(os.environ.get("JWT_SECRET_KEY"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, algorithm=ALGORITHM, lifetime_seconds=3600)

jwt_authentication = AuthenticationBackend(
    name="jwt",
    transport=BearerTransport(tokenUrl="auth/jwt/login"),
    get_strategy=get_jwt_strategy,
)