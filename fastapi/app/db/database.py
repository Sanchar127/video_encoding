import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis

# Load environment variables from .env file
load_dotenv()

# Fetch URLs from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("DRAGONFLY_URL")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Set up Redis client
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)