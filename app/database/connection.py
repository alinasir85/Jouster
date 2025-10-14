import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/knowledge_extractor.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency for getting database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
