import os
import json
import uuid
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
from utils import parse_ranking_from_text, calculate_aggregate_rankings

import re

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "conversations")

# Strict UUID validation regex
UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def list_conversations() -> List[Dict]:
    ensure_data_dir()
    conversations = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Return minimal metadata
                    conversations.append({
                        "id": data.get("id"),
                        "title": data.get("title", "Untitled"),
                        "created_at": data.get("created_at"),
                        # We don't load the full data here to save memory
                        "data": None 
                    })
            except json.JSONDecodeError:
                logger.warning(f"Corrupted file found: {filename}")
                continue
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    # Sort by created_at desc
    conversations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return conversations

def get_conversation(conversation_id: str) -> Optional[Dict]:
    ensure_data_dir()
    
    # Security: Validate ID is a UUID to prevent path traversal.
    if not UUID_REGEX.match(conversation_id):
        logger.warning(f"Invalid conversation ID format attempt blocked: {conversation_id}")
        return None
        
    filepath = os.path.join(DATA_DIR, f"{conversation_id}.json")
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)
            
        # Check if this is the new simple format (has 'data' key with state)
        if "data" in stored_data and isinstance(stored_data["data"], dict):
            return stored_data

        # Fallback for legacy format (transform to new format)
        # This allows old files to still be loaded
        messages = stored_data.get("messages", [])
        user_msg = next((m for m in messages if m["role"] == "user"), None)
        assistant_msg = next((m for m in messages if m["role"] == "assistant"), None)
        
        question = user_msg["content"] if user_msg else ""
        
        stage1_responses = []
        stage2_reviews = []
        stage3_result = None
        selected_models = []
        
        if assistant_msg:
            # Stage 1
            for item in assistant_msg.get("stage1", []):
                stage1_responses.append({
                    "model": item["model"],
                    "response": item["response"]
                })
                selected_models.append(item["model"])
            
            # Stage 2
            for item in assistant_msg.get("stage2", []):
                stage2_reviews.append({
                    "model": item["model"],
                    "review": item["ranking"]
                })
                
            # Stage 3
            s3_data = assistant_msg.get("stage3")
            if s3_data:
                aggregates = calculate_aggregate_rankings(stage1_responses, stage2_reviews)
                stage3_result = {
                    "final_answer": s3_data["response"],
                    "aggregate_rankings": aggregates,
                    "chairman_model": s3_data.get("model")
                }
        
        current_stage = stored_data.get("current_stage", 1)
        if "current_stage" not in stored_data:
            if stage3_result: current_stage = 3
            elif stage2_reviews: current_stage = 2 # Fixed logic: if reviews exist, we are at least stage 2 complete or in progress
            elif stage1_responses: current_stage = 2
            
        return {
            "id": stored_data["id"],
            "title": stored_data["title"],
            "created_at": stored_data["created_at"],
            "data": {
                "id": stored_data["id"],
                "question": question,
                "selectedModels": selected_models,
                "stage1Responses": stage1_responses,
                "stage2Reviews": stage2_reviews,
                "stage3Result": stage3_result,
                "currentStage": current_stage
            }
        }

    except Exception as e:
        logger.error(f"Error reading conversation {conversation_id}: {e}")
        return None

def save_conversation(frontend_state: Dict) -> Dict:
    ensure_data_dir()
    
    conv_id = frontend_state.get("id") or str(uuid.uuid4())
    # Ensure ID is in the state object
    frontend_state['id'] = conv_id

    # Security: Validate ID is a UUID to prevent path traversal.
    if not UUID_REGEX.match(conv_id):
        logger.warning(f"Invalid conversation ID format attempt blocked: {conv_id}")
        return {"error": "Invalid conversation ID"}

    filepath = os.path.join(DATA_DIR, f"{conv_id}.json")
    created_at = datetime.utcnow().isoformat()
    
    # Preserve created_at if updating existing file
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                created_at = existing_data.get("created_at", created_at)
        except Exception as e:
            logger.warning(f"Could not read existing file {filepath} to preserve created_at. Error: {e}")

    title = frontend_state.get("question", "Untitled")[:50]

    # Prepare data to be returned and saved
    # The frontend expects this structure.
    # We store the frontend state directly in "data" to avoid complex transformations.
    response_data = {
        "id": conv_id,
        "title": title,
        "created_at": created_at,
        "data": frontend_state
    }
    
    # Store 'current_stage' at top level for easy access in list_conversations / debugging if needed
    # (Though list_conversations currently only reads metadata)
    response_data["current_stage"] = frontend_state.get("currentStage", 1)

    # Note: We are no longer transforming into the "messages" format (user/assistant). 
    # This simplifies storage but means we rely entirely on the frontend state structure.
    # If the "messages" format was needed for other tools, this would be a breaking change,
    # but for this specific app usage it is cleaner.
    # However, get_conversation ALSO needs to be updated to handle this new simple format
    # OR we must stick to the old format if we want backward compatibility.
    # The Code Review suggestion implies replacing the logic entirely.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, indent=4)
        
    return response_data

def delete_conversation(conversation_id: str) -> bool:
    ensure_data_dir()

    # Security: Validate ID is a UUID to prevent path traversal.
    if not UUID_REGEX.match(conversation_id):
        logger.warning(f"Invalid conversation ID format attempt blocked: {conversation_id}")
        return False
        
    filepath = os.path.join(DATA_DIR, f"{conversation_id}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
    return False
