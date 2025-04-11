from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.encode_profiles import EncodeProfiles, EncodeProfileDetails

def get_profiles_with_details():
    session = SessionLocal()  # Get a session from SessionLocal
    profiles = session.query(EncodeProfiles).all()  # Query all EncodeProfiles

    for profile in profiles:
        print(f"Profile Name: {profile.name}")
        for detail in profile.profile_details:
            print(f"Width: {detail.width}, Height: {detail.height}")
    session.close()
