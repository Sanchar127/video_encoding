from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class EncodeProfiles(Base):
    __tablename__ = "encode_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Assuming there's a users table
    name = Column(String, index=True)
    
    # Relationship to encode profile details
    details = relationship("EncodeProfileDetails", back_populates="profile")

class EncodeProfileDetails(Base):
    __tablename__ = "encode_profile_details"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("encode_profiles.id"))
    width = Column(Integer)
    height = Column(Integer)
    video_bitrate = Column(Integer)
    audio_bitrate = Column(Integer)
    audio_channel = Column(Integer, default=2)
    audio_frequency = Column(String, default="44100")
    sc_threshold = Column(Integer, default=0)
    profile = Column(String, default="high")
    level = Column(Float)
    max_bitrate = Column(Integer)
    bufsize = Column(Integer)
    movflags = Column(String, default="faststart")
    pix_fmt = Column(String, default="yuv420p")
    acodec = Column(String)
    vcodec = Column(String)

    # Relationship to parent profile
    profile = relationship("EncodeProfiles", back_populates="details")
