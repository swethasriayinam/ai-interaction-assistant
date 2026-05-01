from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, func
from database import Base

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