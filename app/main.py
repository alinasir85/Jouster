import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .database import engine, Base

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="LLM Knowledge Extractor",
    description="Extract summaries and structured metadata from text using LLMs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_files_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_files_path), name="static")

# Include API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the web UI."""
    html_path = os.path.join(static_files_path, "index.html")
    with open(html_path, "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/api")
def api_info():
    """API information endpoint."""
    return {
        "message": "Welcome to LLM Knowledge Extractor API",
        "endpoints": {
            "POST /analyze": "Process new text and return analysis",
            "GET /search?topic={topic}": "Search analyses by topic or keyword",
            "GET /analyses": "Get all analyses with pagination",
            "GET /analysis/{id}": "Get specific analysis by ID"
        },
        "web_ui": "Visit / for the web interface"
    }


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input", "detail": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "detail": None}
    )
