from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, relationship, Mapped
from app.core.database import Base


class Aqi5MinuteHistory(Base):
    __tablename__ = "aqi_5_minute_history"
    
    id = Column(Integer, primary_key=True)
    measure_time = Column(DateTime(timezone=True), nullable=False, index=True)
    aqi_location_id = Column(Integer, ForeignKey("aqi_location.id"), nullable=False)
    measure_data: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    location = relationship("AqiLocation", back_populates="history_records")