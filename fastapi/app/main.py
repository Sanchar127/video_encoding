from fastapi import FastAPI
from db.database import Base, engine
from routes import user as user_routes
from routes.encoding import router as encoding_routes
from routes.encodeprofile import router as encode_profile_routes
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
# from services.profile_service import get_profiles_with_details


# @app.get("/profiles")
# def fetch_profiles():
#     get_profiles_with_details()  # Call the function that prints profiles and details
#     return {"message": "Profiles fetched. Check console output."}
app = FastAPI()

# Add CORS middleware to allow cross-origin requests (replace with specific origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (your routes from user, encoding, and encodeprofile)
app.include_router(user_routes.router)
app.include_router(encode_profile_routes)  # Correctly use the router from encodeprofile
app.include_router(encoding_routes, prefix="/encoding")  # Prefix '/encoding' for encoding routes

# Create DB tables at startup
Base.metadata.create_all(bind=engine)
