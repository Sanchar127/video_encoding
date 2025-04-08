from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import redis_client
from models.user import User
from utils.security import verify_password
from uuid import uuid4
from db.database import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def store_token(token: str, user_id: str):
    redis_client.set(f"token:{token}", user_id)

def blacklist_token(token: str):
    redis_client.set(f"blacklist:{token}", "1")
 
def is_token_blacklisted(token: str) -> bool:
    return redis_client.get(f"blacklist:{token}") == "1"

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user
