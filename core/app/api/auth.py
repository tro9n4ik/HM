from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import os
import datetime

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SetupRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/setup")
def setup_admin(req: SetupRequest, db: Session = Depends(get_db)):
    if db.query(User).first() is not None:
        raise HTTPException(status_code=400, detail="Setup already completed")

    user = User(
        username=req.username,
        password_hash=get_password_hash(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Admin user created successfully"}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    secret = os.environ.get("SECRET_KEY", "dev-secret-key")
    payload = {
        "sub": user.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}
