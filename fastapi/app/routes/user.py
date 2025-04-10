import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from fastapi import Query
from schemas.user import UserCreate, UserOut
from models.user import User
from utils.security import hash_password
from db.database import SessionLocal, redis_client
from auth.auth import store_token, authenticate_user

from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# OAuth2 token handler
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API Router
router = APIRouter()


# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Check if the token is blacklisted
    if redis_client.exists(f"blacklisted:{token}"):
        raise HTTPException(status_code=401, detail="Token has been blacklisted")

    user_id = redis_client.get(f"token:{token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.unique_id == user_id).first()
    if not user or not user.is_activated:
        raise HTTPException(status_code=403, detail="User is deactivated or not found")

    return user


# Dependency for admin or super admin access
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
        raise HTTPException(status_code=403, detail="User is deactivated")

    existing_tokens = redis_client.smembers(f"user_tokens:{user.unique_id}")

    valid_access_token = None
    for token in existing_tokens:
        token_str = token.decode() if isinstance(token, bytes) else token
        # Check if token is blacklisted before assigning it as valid
        if redis_client.exists(f"blacklisted:{token_str}"):
            continue  # Skip blacklisted tokens
        if redis_client.exists(f"token:{token_str}"):
            valid_access_token = token_str
            break

    if valid_access_token:
        access_token = valid_access_token
    else:
        access_token = str(uuid4())
        store_token(access_token, user.unique_id)

    refresh_token = str(uuid4())
    store_token(refresh_token, user.unique_id, is_refresh=True)

    response = JSONResponse(content={
        "access_token": access_token,
        "token_type": "bearer"
    })
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    return response



# USERS: Get all users

@router.get("/users", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    return db.query(User).all()


# USERS: Create user

@router.post("/users/create", response_model=UserOut)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # Check for duplicate email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Role validation
    if user_data.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot create super admin")

    if user_data.role == "admin" and current_user.role == "user":
        raise HTTPException(status_code=403, detail="Only admin and super admins can create admins")

    new_user = User(
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

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



# USERS: Update user

@router.put("/users/update/{user_id}", response_model=UserOut)
def update_user(user_id: str, user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    db_user = db.query(User).filter(User.unique_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Role restriction
    if db_user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admins can update super admins")

    if current_user.role == "admin":
        if user_data.role == "admin" and current_user.unique_id != db_user.unique_id:
            raise HTTPException(status_code=403, detail="Admins can only update themselves")
        if user_data.role == "super_admin":
            raise HTTPException(status_code=403, detail="Admins cannot assign super admin role")

    # Email duplication check
    if db.query(User).filter(User.email == user_data.email, User.unique_id != user_id).first():
        raise HTTPException(status_code=400, detail="Email already in use")

    # Update user details
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

    db.commit()
    db.refresh(db_user)
    return db_user




@router.post("/users/blacklist-token/{user_id}")
def blacklist_user_token(
    user_id: str,
    duration_minutes: int = Query(None, description="Duration in minutes to blacklist the token"),
    current_user: User = Depends(get_admin_user)
):
    # Step 1: Fetch tokens from Redis
    tokens = redis_client.smembers(f"user_tokens:{user_id}")

    # Step 2: If no tokens found, raise 404
    if not tokens:
        raise HTTPException(status_code=404, detail="No tokens found in Redis for this user")

    # Step 3: Role-based restrictions
    if current_user.role == "admin" and user_id != current_user.unique_id:
        raise HTTPException(status_code=403, detail="Admins can only revoke their own token")

# Step 4: Blacklist tokens
    for token in tokens:
        token_str = token.decode() if isinstance(token, bytes) else token
        redis_client.set(f"blacklisted:{token_str}", "1", ex=duration_minutes * 60 if duration_minutes else None)
        redis_client.sadd("blacklisted_tokens", token_str)  
        redis_client.set(f"token:{token_str}", user_id)      

       

    return {
        "message": f"Tokens for user {user_id} have been blacklisted",
        "duration_minutes": duration_minutes if duration_minutes else "permanently"
    }



@router.get("/blacklisted-tokens/details")
def get_blacklisted_token_details():
    tokens = redis_client.smembers("blacklisted_tokens")
    details = []
    for token in tokens:
        token_str = token.decode() if isinstance(token, bytes) else token

      
        user_id = redis_client.get(f"token:{token_str}")
        if user_id:
            user_id = user_id.decode() if isinstance(user_id, bytes) else user_id

        
        ttl_seconds = redis_client.ttl(f"blacklisted:{token_str}")

      
        if ttl_seconds == -1:
            duration = "permanent"
        elif ttl_seconds == -2:
            duration = "expired"
        else:
            duration = f"{ttl_seconds // 60} minutes"

        details.append({
            "token": token_str,
            "user_id": user_id,
            "remaining_duration": duration
        })

    return {"blacklisted_tokens": details}

@router.get("/tokens/stored")
def get_all_stored_tokens():
    keys = redis_client.keys("token:*")
    tokens = []
    for key in keys:
        token = key.decode().replace("token:", "") if isinstance(key, bytes) else key.replace("token:", "")
        user_id = redis_client.get(key)
        if user_id:
            user_id = user_id.decode() if isinstance(user_id, bytes) else user_id
        tokens.append({"token": token, "user_id": user_id})
    return {"stored_tokens": tokens}



