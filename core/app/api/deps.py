from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
import os
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

# Not strictly needed since we are migrating to cookies, but kept for compatibility during refactoring
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user_from_token(token: str, db: Session) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY environment variable is not set")

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)):
    # Try reading from cookie first
    token = request.cookies.get("access_token")
    if not token:
        # Fallback to authorization header (for legacy or API usage)
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return get_current_user_from_token(token, db)
