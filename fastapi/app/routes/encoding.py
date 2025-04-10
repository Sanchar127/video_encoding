from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
import uuid
import ffmpeg
import os
from dotenv import load_dotenv
import shutil
from db.database import Base, engine
from db.database import SessionLocal, redis_client

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI setup
router = APIRouter()

class VideoJob(Base):
    __tablename__ = "video_jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    video_filename = Column(String(255), index=True)
    encoding_profile = Column(Integer)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class EncodingProfile:
    def __init__(self, name: str, width: int, height: int, video_bitrate: int, audio_bitrate: int,
                 audio_channel: int, audio_frequency: str, sc_threshold: int, profile: str,
                 level: float, max_bitrate: int, bufsize: int, movflags: str, pix_fmt: str,
                  acodec: str, vcodec: str):
        self.name = name
        self.width = width
        self.height = height
        self.video_bitrate = video_bitrate
        self.audio_bitrate = audio_bitrate
        self.audio_channel = audio_channel
        self.audio_frequency = audio_frequency
        self.sc_threshold = sc_threshold
        self.profile = profile
        self.level = level
        self.max_bitrate = max_bitrate
        self.bufsize = bufsize
        self.movflags = movflags
        self.pix_fmt = pix_fmt
        # self.force_format = force_format
        self.acodec = acodec
        self.vcodec = vcodec


encoding_profile_1080p = EncodingProfile(
    name="1080p",
    width=1920,
    height=1080,
    video_bitrate=5000,
    audio_bitrate=192,
    audio_channel=2,
    audio_frequency="44100",
    sc_threshold=0,
    profile="high",
    level=4.1,
    max_bitrate=10000,
    bufsize=2000,
    movflags="faststart",
    pix_fmt="yuv420p",
    # force_format="mp4",
    acodec="aac",
    vcodec="libx264"
)

# Endpoint to upload video and process encoding
@router.put("/upload_video/{user_id}")
async def upload_video(user_id: int, video: UploadFile = File(...), db: Session = Depends(get_db)):
    video_filename = f"{uuid.uuid4()}_{video.filename}"
    video_path = f"./videos/{video_filename}"

    # Make sure the video directory exists
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    # Save uploaded video to local file system
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # Create a VideoJob entry in the database
    video_job = VideoJob(
        user_id=user_id,
        video_filename=video_filename,
        encoding_profile=1,  # Using static encoding profile (ID=1 for 1080p profile)
        status="queued",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(video_job)
    db.commit()
    db.refresh(video_job)

    # Process the video encoding (blocking for now)
    process_video_encoding(video_job, db)
    return {"message": "Video uploaded and encoding started", "job_id": video_job.id}


def process_video_encoding(video_job, db):
    encoding_profile = encoding_profile_1080p

    try:
        output_path = f"./videos/{video_job.video_filename.replace('.mp4', f'_{encoding_profile.name}_encoded.mp4')}"

        # Use FFmpeg to encode the video
        ffmpeg.input(f"./videos/{video_job.video_filename}").output(
            output_path,
            vcodec=encoding_profile.vcodec,
            acodec=encoding_profile.acodec,
            s=f"{encoding_profile.width}x{encoding_profile.height}",
            bitrate=f"{encoding_profile.video_bitrate}k",
            audio_bitrate=f"{encoding_profile.audio_bitrate}k",
            ac=encoding_profile.audio_channel,
            ar=encoding_profile.audio_frequency,
            level=encoding_profile.level,
            maxrate=f"{encoding_profile.max_bitrate}k",
            bufsize=f"{encoding_profile.bufsize}k",
            movflags=encoding_profile.movflags,
            pix_fmt=encoding_profile.pix_fmt,
            # force_format=encoding_profile.force_format
        ).run()

        # Update the job status to completed in the database
        video_job.status = "completed"
        video_job.updated_at = datetime.utcnow()
        db.commit()

        send_job_completion_notification(video_job)
    except ffmpeg.Error as e:
        print(f"FFmpeg error occurred: {e}")
        video_job.status = "failed"
        video_job.updated_at = datetime.utcnow()
        db.commit()
        send_job_failure_notification(video_job)
    except ffmpeg._run.Error as e:
        print(f"FFmpeg encoding error: {e.stderr.decode()}")
        video_job.status = "failed"
        video_job.updated_at = datetime.utcnow()
        db.commit()
        send_job_failure_notification(video_job)
    except FileNotFoundError as e:
        print(f"File error: {str(e)}")
        video_job.status = "failed"
        video_job.updated_at = datetime.utcnow()
        db.commit()
        send_job_failure_notification(video_job)
    except Exception as e:
        print(f"Unknown error: {str(e)}")
        video_job.status = "failed"
        video_job.updated_at = datetime.utcnow()
        db.commit()
        send_job_failure_notification(video_job)


def send_job_completion_notification(video_job):
    print(f"Job {video_job.id} completed successfully!")

def send_job_failure_notification(video_job):
    print(f"Job {video_job.id} failed!")

# Admin endpoint to initialize the system
@router.get("/admin/init")
async def init_admin(db: Session = Depends(get_db)):
    if not db.query(VideoJob).filter(VideoJob.status == "queued").first():
        return {"message": "Please configure the super admin account"}
    return {"message": "System initialized"}
