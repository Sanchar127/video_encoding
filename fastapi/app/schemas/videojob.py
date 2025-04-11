from pydantic import BaseModel
from datetime import datetime

class VideoJobRead(BaseModel):
    id: int
    video_filename: str
    encoding_profile: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
