from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notification"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    email = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)