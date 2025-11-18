# File: ielts-scorer/app/database.py
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ielts_scorer.db")

if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

def create_engine_with_retry(db_url, retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            engine = create_engine(
                db_url,
                pool_pre_ping=True,         # kiểm tra connection trước khi dùng
                connect_args={"connect_timeout": 5} if "postgres" in db_url else {},
            )
            # thử connect
            with engine.connect() as conn:
                print("Database connected successfully.")
            return engine
        except OperationalError as e:
            print(f"[DB Retry] Attempt {attempt}/{retries} failed: {e}")
            time.sleep(delay)

    raise RuntimeError("❌ Could not connect to the database after retries.")


engine = create_engine_with_retry(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
