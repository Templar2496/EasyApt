from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .database import init_db
from . import models
from .auth import router as auth_router
from .profile import router as profile_router
from .appointments import router as appointments_router

app = FastAPI(title="EasyApt API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Include API routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(profile_router, prefix="/profile", tags=["profiles"])
app.include_router(appointments_router, tags=["appointments & providers"])

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Path to frontend directory
frontend_path = Path(__file__).parent.parent.parent / "frontend"

# Mount static files (CSS, JS)
app.mount("/css", StaticFiles(directory=str(frontend_path / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(frontend_path / "js")), name="js")

# Serve HTML pages
@app.get("/")
async def serve_home():
    return FileResponse(str(frontend_path / "index.html"))

@app.get("/login.html")
async def serve_login():
    return FileResponse(str(frontend_path / "login.html"))

@app.get("/register.html")
async def serve_register():
    return FileResponse(str(frontend_path / "register.html"))

@app.get("/profile.html")
async def serve_profile():
    return FileResponse(str(frontend_path / "profile.html"))

@app.get("/appointments.html")
async def serve_appointments():
    return FileResponse(str(frontend_path / "appointments.html"))

@app.get("/book-appointment.html")
async def serve_book_appointment():
    return FileResponse(str(frontend_path / "book-appointment.html"))

@app.get("/provider-dashboard.html")
async def serve_provider_dashboard():
    return FileResponse(str(frontend_path / "provider-dashboard.html"))
