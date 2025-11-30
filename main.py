"""
Monorama Polyclinic - Prescription Management System
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# Create FastAPI app
app = FastAPI(
    title="Monorama Polyclinic",
    description="Prescription Management System with OCR",
    version="1.0.0"
)

# CORS middleware - allows requests from any origin (needed for mobile browsers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Monorama Polyclinic API is running",
        "version": "1.0.0"
    }

# Health check for Cloud Run
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Import routers
from routers import ocr, prescriptions, auth
app.include_router(ocr.router)
app.include_router(prescriptions.router)
app.include_router(auth.router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
