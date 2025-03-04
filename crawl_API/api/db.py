from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Create SQLAlchemy engine
DATABASE_URL = "mysql+mysqlconnector://root@localhost/nrlm_data"
engine = create_engine(DATABASE_URL)

# Create base class for ORM models
Base = declarative_base()

# Define ORM models
class SpecifiedTable(Base):
    __tablename__ = "villaname"
    
    id = Column(Integer, primary_key=True, index=True)
    statename = Column(String(255), index=True)
    districtname = Column(String(255), index=True)
    blockname = Column(String(255), index=True)
    gpname = Column(String(255), index=True)
    villname = Column(String(255), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ScrapeLog(Base):
    __tablename__ = "scrapelog"
    
    id_num = Column(Integer, primary_key=True, index=True)
    dis_index = Column(Integer)
    districtname = Column(String(255))
    blk_index = Column(Integer)
    blockname = Column(String(255))
    gp_index = Column(Integer)
    gpname = Column(String(255))
    scrape_success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()