from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db.database import Base

class VideoJob(Base):
    __tablename__ = 'video_jobs'

    id = Column(Integer, primary_key=True, index=True)
    video_filename = Column(String(220), nullable=False)
    encoding_profile = Column(Integer, ForeignKey("encode_profiles.id"), nullable=False)
    status = Column(String(200), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # Relationship to EncodeProfiles
    encode_profile = relationship("EncodeProfiles", back_populates="video_jobs")
