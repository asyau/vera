from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.routes import conversation, openai_service

app = FastAPI(
    title="Vira API",
    description="Backend API for Vira, the AI-powered assistant platform for teams",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(conversation.router, prefix="/api", tags=["conversation"])
app.include_router(openai_service.router, prefix="/api", tags=["openai"])

@app.get("/")
async def root():
    return {"message": "Welcome to Vira API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 