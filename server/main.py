import logging
import os
import re
import sys
from dotenv import load_dotenv

load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        msg = str(record.msg)
        # Redact known keys
        keys_to_redact = [
            os.getenv("GEMINI_API_KEY"),
            os.getenv("GEMINI_CUSTOM_KEY")
        ]
        for key in keys_to_redact:
            if key and len(key) > 5: # Only redact if key is substantial to avoid masking short common words
                msg = msg.replace(key, "***REDACTED***")
        
        # Redact patterns in URLs (e.g. ?key=xyz)

        msg = re.sub(r'(key|api_key)=([a-zA-Z0-9_\-]+)', r'\1=***REDACTED***', msg)
        
        record.msg = msg
        return True

# Handlers
stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("logs/app.log", encoding='utf-8')

# Apply filter
sensitive_filter = SensitiveDataFilter()
stream_handler.addFilter(sensitive_filter)
file_handler.addFilter(sensitive_filter)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[stream_handler, file_handler]
)
logger = logging.getLogger("llm_council")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import storage
from models import SynthesisRequest, SynthesisResponse, ConversationCreate, Conversation
from services.gemini_service import synthesize_answer

app = FastAPI(title="LLM Council API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Perform one-time database initialization and migration on startup."""
    storage._migrate_json_files_if_needed()
    logger.info("Database startup initialization completed")

@app.get("/")
def read_root():
    return {"message": "Welcome to LLM Council API"}

@app.post("/api/synthesize", response_model=SynthesisResponse)
async def synthesize(request: SynthesisRequest):
    # 1. Generate Synthesis
    result = await synthesize_answer(request)
    
    # 2. Auto-Save Conversation
    # Construct the full conversation state to save
    conversation_state = {
        "id": request.id,
        "question": request.question,
        "selectedModels": [r.model for r in request.stage1_responses],
        "stage1Responses": [r.dict() for r in request.stage1_responses],
        "stage2Reviews": [r.dict() for r in request.stage2_reviews],
        "stage3Result": result.dict(),
        "currentStage": 3
    }
    
    try:
        storage.save_conversation(conversation_state)
        logger.info(f"Auto-saved conversation {request.id}")
    except Exception as e:
        logger.error(f"Failed to auto-save conversation: {e}")

    return result

@app.get("/api/conversations", response_model=List[Dict[str, Any]])
def get_conversations():
    return storage.list_conversations()

@app.post("/api/conversations", response_model=Dict[str, Any])
def create_conversation(conversation: ConversationCreate):
    # The frontend sends 'data' which is the ConversationState
    # We pass this directly to storage.save_conversation
    return storage.save_conversation(conversation.data)

@app.get("/api/conversations/{conversation_id}", response_model=Dict[str, Any])
def get_conversation(conversation_id: str):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    success = storage.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or could not be deleted")
    return {"message": "Conversation deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
