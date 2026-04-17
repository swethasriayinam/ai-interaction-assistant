from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, func
from database import Base
from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String, nullable=False)
    interaction_type = Column(String)
    date = Column(Date)
    time = Column(Time)
    attendees = Column(Text)
    topics = Column(Text)
    materials_shown = Column(Text)
    samples_distributed = Column(Text)
    outcome = Column(Text)
    follow_up = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class InteractionBase(BaseModel):
    hcp_name: str
    interaction_type: Optional[str] = None
    date: Optional[date] = None
    time: Optional[time] = None
    attendees: Optional[str] = None
    topics: Optional[str] = None
    materials_shown: Optional[str] = None
    samples_distributed: Optional[str] = None
    outcome: Optional[str] = None
    follow_up: Optional[str] = None
    notes: Optional[str] = None

class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True