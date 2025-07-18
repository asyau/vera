from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
import logging

import sentry_sdk
from pydantic import ValidationError

sentry_sdk.init(
    dsn="https://d436c015096491c747000cb1fd120cf3@o4509151357829120.ingest.de.sentry.io/4509151366676560",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)


# Load environment variables from .env file
load_dotenv()

from app.routes import conversation, openai_service, task, user

app = FastAPI(
    title="Vera API",
    description="API for Vera AI Assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:8080", 
        "https://localhost:8080",
        "http://127.0.0.1:8080",
        "https://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Include routers
app.include_router(conversation.router, prefix="/api", tags=["conversation"])
app.include_router(openai_service.router, prefix="/api", tags=["openai"])
app.include_router(task.router, prefix="/api", tags=["tasks"])
app.include_router(user.router, prefix="/api", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to Vera API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.options("/api/tasks")
async def tasks_options():
    """Handle preflight requests for tasks endpoint"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 