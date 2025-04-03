from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.routes import conversation, openai_service, task

app = FastAPI(
    title="Vera API",
    description="API for Vera AI Assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "https://localhost:8080"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(conversation.router, prefix="/api", tags=["conversation"])
app.include_router(openai_service.router, prefix="/api", tags=["openai"])
app.include_router(task.router, prefix="/api", tags=["tasks"])

@app.get("/")
async def root():
    return {"message": "Welcome to Vera API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 