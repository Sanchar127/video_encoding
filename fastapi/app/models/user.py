from sqlalchemy import Column, String, Boolean, Integer
from uuid import uuid4
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(36), default=lambda: str(uuid4()), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    callback_key = Column(String(200), nullable=False)
    callback_url = Column(String(200), nullable=False)
    callback_secret_key = Column(String(200), nullable=False)
    stream_url = Column(String(255))
    is_activated = Column(Boolean, default=False)
    status = Column(Boolean, default=False)
    email_notification_status = Column(Boolean, default=True)
    email_notification = Column(Boolean, default=True)
    mobile = Column(String(20), nullable=False)
    address = Column(String(255))
    role = Column(String(20), nullable=False, default="user")
