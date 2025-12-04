"""
Start EasyAPT Development Server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api_endpoints import router

app = FastAPI(
    title="EasyAPT - Emil's Components",
    description="Notification, CAPTCHA, Time Handling, and Test Profile Services",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "EasyAPT API - Emil's Components",
        "version": "1.0.0",
        "status": "running",
        "components": [
            "Notification Service",
            "CAPTCHA Service", 
            "Time Handler",
            "Test Profile Service"
        ],
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "easyapt-emil"}

if __name__ == "__main__":
    print("\n" + "="*70)
    print("STARTING EASYAPT API SERVER")
    print("="*70)
    print("\nAPI Running at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    uvicorn.run(
        "start_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
