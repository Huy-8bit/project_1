from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .accesstoken import verify_access_token
from app.core.accesstoken import verify_access_token, check_user_exit

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    decoded_jwt = verify_access_token(token)
    if not decoded_jwt:
        raise credentials_exception
    user_id = decoded_jwt.get("sub")
    if user_id is None or not check_user_exit(user_id):
        raise credentials_exception
    return user_id
