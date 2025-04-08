import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserOut
from models.user import User
from utils.security import hash_password
from db.database import SessionLocal
from auth.auth import store_token, authenticate_user
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from uuid import uuid4
from db.database import redis_client



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Fetch user ID from Redis using the token
    user_id = redis_client.get(f"token:{token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.unique_id == user_id).first()
    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    return current_user

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.is_activated:
        raise HTTPException(status_code=403, detail="User not activated")
    token = str(uuid4())
    store_token(token, user.unique_id)
    return {"access_token": token, "token_type": "bearer","is_activated":user.is_activated}



@router.post("/users/create", response_model=UserOut)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Role validation logic
    if user_data.role == "super_admin":
        raise HTTPException(status_code=403, detail="Do not have privileges to create super admin")
    
    if user_data.role == "admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Admins don't have privilege to create another admin")

    db_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(user_data.password),
        mobile=user_data.mobile,
        address=user_data.address,
        role=user_data.role,
        stream_url=user_data.stream_url,
        callback_url=user_data.callback_url,
        callback_key=user_data.callback_key,
        callback_secret_key=user_data.callback_secret_key,
        is_activated=True,
        status=True,
        email_notification_status=True,
        email_notification=True
    )
  


@router.put("/users/update/{user_id}", response_model=UserOut)
def update_user(user_id: str, user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    db_user = db.query(User).filter(User.unique_id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent updating super_admin by non-super_admin
    if current_user.role != "super_admin" and db_user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Only super admins can update super admins")

    if current_user.role == "admin" and db_user.role == "admin" and current_user.unique_id != db_user.unique_id:
        raise HTTPException(status_code=403, detail="Admins can only update their own data")

    # Check if the new email is already used by another user
    email_exists = db.query(User).filter(User.email == user_data.email, User.unique_id != user_id).first()
    if email_exists:
        raise HTTPException(status_code=400, detail="Email already in use by another user")

    # Update user data
    db_user.name = user_data.name
    db_user.email = user_data.email
    db_user.password = hash_password(user_data.password) if user_data.password else db_user.password
    db_user.mobile = user_data.mobile
    db_user.address = user_data.address
    db_user.role = user_data.role if current_user.role == "super_admin" else db_user.role
    db_user.stream_url = user_data.stream_url
    db_user.callback_url = user_data.callback_url
    db_user.callback_key = user_data.callback_key
    db_user.callback_secret_key = user_data.callback_secret_key
    db_user.is_activated = user_data.is_activated if current_user.role in ("super_admin", "admin") else db_user.is_activated
    db_user.status = user_data.status
    db_user.email_notification_status = user_data.email_notification_status
    db_user.email_notification = user_data.email_notification



    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

    