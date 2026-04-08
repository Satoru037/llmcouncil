from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Stage1Response(BaseModel):
    model: str
    response: str

class Stage2Review(BaseModel):
    model: str
    review: str

class SynthesisRequest(BaseModel):
    id: Optional[str] = None
    question: str
    stage1_responses: List[Stage1Response]
    stage2_reviews: List[Stage2Review]

class AggregateRanking(BaseModel):
    model: str
    avg_rank: float
    votes: int

class SynthesisResponse(BaseModel):
    final_answer: str
    aggregate_rankings: List[AggregateRanking]
    chairman_model: Optional[str] = None

class ConversationState(BaseModel):
    id: Optional[str] = None
    question: str
    selectedModels: List[str]
    stage1Responses: List[Stage1Response]
    stage2Reviews: List[Stage2Review]
    stage3Result: Optional[SynthesisResponse] = None
    currentStage: int

class ConversationCreate(BaseModel):
    title: str
    question: str
    data: ConversationState

class Conversation(ConversationCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
