from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from db.database import Base

class EncodeProfiles(Base):
    __tablename__ = 'encode_profiles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)

    # Relationship to VideoJob model, assuming it's defined elsewhere
    video_jobs = relationship("VideoJob", back_populates="encode_profile")

    # Relationship to EncodeProfileDetails model, with cascade for delete-orphan
    profile_details = relationship(
        "EncodeProfileDetails",
        back_populates="parent_profile",
        cascade="all, delete-orphan"
    )

class EncodeProfileDetails(Base):
    __tablename__ = "encode_profile_details"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("encode_profiles.id"), nullable=False)

    # Encoding settings fields
    width = Column(Integer)
    height = Column(Integer)
    video_bitrate = Column(Integer)
    audio_bitrate = Column(Integer)
    audio_channel = Column(Integer, default=2)
    audio_frequency = Column(String(50), default="44100")
    sc_threshold = Column(Integer, default=0)
    profile = Column(String(50), default="high")
    level = Column(Float)
    max_bitrate = Column(Integer)
    bufsize = Column(Integer)
    movflags = Column(String(50), default="faststart")
    pix_fmt = Column(String(50), default="yuv420p")
    acodec = Column(String(50))
    vcodec = Column(String(50))

    # Relationship to EncodeProfiles, so we can access profile name from here
    parent_profile = relationship("EncodeProfiles", back_populates="profile_details")

