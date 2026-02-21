from sqlalchemy import create_all, Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(String, primary_key=True)
    name = Column(String)
    spec = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"))
    status = Column(String) # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Trace(Base):
    __tablename__ = "traces"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id"))
    events = Column(JSON) # List of events

engine = create_engine("sqlite:///./langpedia.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
