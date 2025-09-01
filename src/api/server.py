from dotenv import load_dotenv
import os
load_dotenv()
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.dependencies.configure_container import configure_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_container()  
    yield

app = FastAPI(lifespan=lifespan)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "https://expertise-ai-tan.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Internal"])
async def health():
    """
    ## Health check 
    This endpoints verifies server status.
    """
    return {"status": "ok"}


