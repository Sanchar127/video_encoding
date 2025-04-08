from fastapi import FastAPI
from db.database import Base, engine
from routes import user as user_routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()  # ✅ Define app first!

# ✅ Then add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include your routers
app.include_router(user_routes.router)

# ✅ Create DB tables
Base.metadata.create_all(bind=engine)
