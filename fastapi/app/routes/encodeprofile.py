from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.database import get_db, SessionLocal
from models.encodeprofile import EncodeProfiles, EncodeProfileDetails
from schemas.encodeprofile import EncodeProfileCreate, EncodeProfileDetailsCreate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/encode-profile", response_model=EncodeProfileCreate)
async def create_encode_profile(profile: EncodeProfileCreate, db: Session = Depends(get_db)):
    db_profile = EncodeProfiles(name=profile.name)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.post("/encode-profile-details", response_model=EncodeProfileDetailsCreate)
async def create_encode_profile_details(details: EncodeProfileDetailsCreate, db: Session = Depends(get_db)):
    db_profile = db.query(EncodeProfiles).filter(EncodeProfiles.id == details.profile_id).first()

    if not db_profile:
        raise HTTPException(status_code=404, detail="Encode Profile not found")

    db_profile_details = EncodeProfileDetails(
        profile_id=details.profile_id,
        width=details.width,
        height=details.height,
        video_bitrate=details.video_bitrate,
        audio_bitrate=details.audio_bitrate,
        audio_channel=details.audio_channel,
        audio_frequency=details.audio_frequency,
        sc_threshold=details.sc_threshold,
        profile=details.profile,
        level=details.level,
        max_bitrate=details.max_bitrate,
        bufsize=details.bufsize,
        movflags=details.movflags,
        pix_fmt=details.pix_fmt,
        acodec=details.acodec,
        vcodec=details.vcodec,
    )
    db.add(db_profile_details)
    db.commit()
    db.refresh(db_profile_details)

    return db_profile_details
