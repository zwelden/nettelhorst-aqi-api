from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AqiLocation(Base):
    __tablename__ = "aqi_location"
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, nullable=False)
    location_name = Column(Text, nullable=False)
    location_description = Column(Text, nullable=False)
    serial_no = Column(String(24), nullable=False)
    model = Column(String(120), nullable=False)
    firmware_version = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    history_records = relationship("Aqi5MinuteHistory", back_populates="location")