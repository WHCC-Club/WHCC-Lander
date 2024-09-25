from sqlalchemy import create_engine, Column, Integer, String, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database Setup
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    discord_id = Column(String, unique=True, index=True)
    score = Column(Integer, default=0)
    challenges = Column(JSON)
    roles = Column(JSON)

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    url = Column(String)
    hint = Column(String)
    flag = Column(String)
    points = Column(Integer)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)
