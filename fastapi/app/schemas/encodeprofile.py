from pydantic import BaseModel

class EncodeProfileCreate(BaseModel):
    name: str

class EncodeProfileDetailsCreate(BaseModel):
    profile_id: int
    width: int
    height: int
    video_bitrate: int
    audio_bitrate: int
    audio_channel: int
    audio_frequency: str
    sc_threshold: int
    profile: str
    level: float
    max_bitrate: int
    bufsize: int
    movflags: str
    pix_fmt: str
    acodec: str
    vcodec: str

    class Config:
        orm_mode = True
