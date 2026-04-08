
import os
import google.generativeai as genai
from dotenv import load_dotenv
from models import SynthesisResponse, AggregateRanking, SynthesisRequest
import re
from typing import List, Dict
import logging
from utils import calculate_aggregate_rankings

import httpx
import json
from fastapi import HTTPException

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def get_model():
    model_name = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
    return genai.GenerativeModel(model_name)



async def synthesize_answer(request_data: SynthesisRequest) -> SynthesisResponse:
    # 1. Construct the prompt (Same as before)
    question = request_data.question
    responses = request_data.stage1_responses
    reviews = request_data.stage2_reviews

    prompt_text = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {question}

STAGE 1 - Individual Responses:
"""
    
    letter_to_model = {}
    for i, r in enumerate(responses):
        letter = chr(65 + i) # A, B, C...
        letter_to_model[f"Response {letter}"] = r.model
        prompt_text += f"\nModel: {r.model}\nResponse: {r.response}\n"

    prompt_text += "\nSTAGE 2 - Peer Rankings:\n"
    
    for r in reviews:
        prompt_text += f"\nModel: {r.model}\nRanking: {r.review}\n"

    prompt_text += """
Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:
"""

    logger.debug(f"Generated Prompt: {prompt_text}")
    # 2. Call API (Custom or Standard)
    custom_key = os.getenv("GEMINI_CUSTOM_KEY")
    endpoint = os.getenv("GEMINI_CUSTOM_ENDPOINT")

    # Fail fast with a clear message when no supported auth configuration is present.
    # Without this, the SDK may fall back to ambient credentials and return opaque scope errors.
    if not ((custom_key and endpoint) or API_KEY):
        logger.error("Gemini credentials missing: set GEMINI_API_KEY or GEMINI_CUSTOM_ENDPOINT+GEMINI_CUSTOM_KEY")
        raise HTTPException(
            status_code=500,
            detail=(
                "Gemini credentials are not configured. "
                "Set GEMINI_API_KEY in server/.env, or set both GEMINI_CUSTOM_ENDPOINT and GEMINI_CUSTOM_KEY."
            ),
        )
    
    final_answer = ""
    custom_error = None
    
    # CASE A: Custom Endpoint (e.g. Thinking Model Proxy)
    if custom_key and endpoint:
        try:
            url = f"{endpoint}?key={custom_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
                "generationConfig": {
                    "temperature": 1,
                    "maxOutputTokens": 65535,
                    "topP": 0.95,
                    "thinkingConfig": {"thinkingLevel": "HIGH"}
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                ]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=60.0)
                if response.status_code != 200:
                    logger.error(f"Custom API Error {response.status_code}: {response.text}")
                    custom_error = HTTPException(status_code=502, detail="Failed to get a valid response from the synthesis model.")
                else:
                    data = response.json()
                    # Handle both single object and list of chunks
                    if isinstance(data, dict): data = [data] 
                    for chunk in data:
                        if "candidates" in chunk:
                            for candidate in chunk["candidates"]:
                                if "content" in candidate and "parts" in candidate["content"]:
                                    for part in candidate["content"]["parts"]:
                                        if "text" in part:
                                            final_answer += part["text"]
        except httpx.RequestError as e:
            logger.error(f"Custom API Request Error: {e}")
            custom_error = HTTPException(status_code=502, detail=f"Custom API Connection Error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Custom API Invalid JSON: {e}")
            custom_error = HTTPException(status_code=502, detail="Custom API returned invalid JSON")
        except Exception as e:
            logger.error(f"Custom API Unexpected Error: {e}")
            custom_error = HTTPException(status_code=500, detail=f"Custom API Error: {str(e)}")

    # CASE B: Standard Gemini SDK (Fallback)
    if not final_answer and API_KEY:
        if custom_error:
            logger.warning("Custom endpoint failed; falling back to standard GEMINI_API_KEY flow")
        try:
            model = get_model()
            # Generate content
            response = await model.generate_content_async(prompt_text)
            final_answer = response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")

    if not final_answer and custom_error:
        raise custom_error


    # 3. Calculate Rankings
    # Use utility function to ensure consistency and deduplication
    aggregate_rankings_dicts = calculate_aggregate_rankings(
        [r.dict() for r in responses],
        [r.dict() for r in reviews]
    )
    # Convert back to Pydantic models
    aggregate_rankings = [AggregateRanking(**d) for d in aggregate_rankings_dicts]

    # Determine model name for response
    chairman_name = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")

    return SynthesisResponse(
        final_answer=final_answer,
        aggregate_rankings=aggregate_rankings,
        chairman_model=chairman_name
    )
