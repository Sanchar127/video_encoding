from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import ffmpeg
import os
import shutil
from db.database import SessionLocal
from models.encodeprofile import EncodeProfileDetails
from models.videojob import VideoJob

# FastAPI setup
router = APIRouter()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.put("/upload_video")
async def upload_video(video: UploadFile = File(...), db: Session = Depends(get_db)):
    video_filename = f"{uuid.uuid4()}_{video.filename}"
    video_path = f"./videos/{video_filename}"

    # Ensure the video directory exists
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    # Save uploaded video
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # Create a VideoJob entry in the database without user_id
    video_job = VideoJob(
        video_filename=video_filename,
        encoding_profile=1,  # Static encoding profile (you can modify this)
        status="queued",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(video_job)
    db.commit()
    db.refresh(video_job)

    # Process the video encoding (blocking)
    process_video_encoding(video_job, db)

    return {"message": "Video uploaded and encoding started", "job_id": video_job.id}


def process_video_encoding(video_job, db):
    encoding_profile = db.query(EncodeProfileDetails).filter(
        EncodeProfileDetails.profile_id == video_job.encoding_profile
    ).first()

    if not encoding_profile:
        print("Encoding profile not found!")
        video_job.status = "failed"
        video_job.updated_at = datetime.utcnow()
        db.commit()
        send_job_failure_notification(video_job)
        return

    video_path = f"./videos/{video_job.video_filename}"
    output_path = f"./videos/{video_job.video_filename.replace('.mp4', f'_{encoding_profile.profile}_encoded.mp4')}"

    if not video_job.video_filename.lower().endswith(".mp4"):
        video_job.status = "failed"
        video_job.updated_at = datetime.utcnow()
        db.commit()
        send_job_failure_notification(video_job)
        return {"message": "Only MP4 files are allowed."}

    try:
        # Use FFmpeg to encode the video
        ffmpeg.input(video_path).output(
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
        ).run()

        video_job.status = "completed"
        video_job.updated_at = datetime.utcnow()
        db.commit()

        send_job_completion_notification(video_job)

    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e}")
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
