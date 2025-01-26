from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import os
from orchestration_agent import orchestration_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('app.log')  # File handler
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv()

def verify_environment():
    """Verify that the environment is properly set up."""
    # Check if PATH is properly set
    path = os.environ.get('PATH', '')
    if not path:
        raise RuntimeError("PATH environment variable is not set")
    
    # Log the current PATH for debugging
    logger.info("Current PATH: " + path)
    
    # Check if OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

# Initialize FastAPI application
logger.info("FastAPI application initialized")
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Verify environment and required tools on startup."""
    try:
        verify_environment()
    except Exception as e:
        logger.error(f"Environment verification failed: {str(e)}")
        raise RuntimeError(f"Application startup failed: {str(e)}")

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/process_query")
async def process_query(request: QueryRequest):
    """Process an infrastructure management query."""
    try:
        return StreamingResponse(
            orchestration_agent.process_query(request.query),
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run(app, host="0.0.0.0", port=8000) 