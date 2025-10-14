from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to analyze")

    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v):
        if not v or v.isspace():
            raise ValueError('Text cannot be empty or only whitespace')
        return v


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary: str
    title: Optional[str]
    topics: List[str]
    sentiment: str
    keywords: List[str]
    confidence_score: Optional[int]
    created_at: datetime


class SearchResponse(BaseModel):
    analyses: List[AnalysisResponse]
    total_count: int
    search_term: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
