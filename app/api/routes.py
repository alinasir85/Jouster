import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db, Analysis
from ..schemas import AnalyzeRequest, AnalysisResponse, SearchResponse
from ..services import LLMService, TextProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services lazily to ensure environment is loaded
_llm_service = None
_text_processor = None


def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_text_processor():
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(
        request: AnalyzeRequest,
        db: Session = Depends(get_db)
):
    """
    Analyze text to generate summary and extract metadata.
    
    Handles edge cases:
    - Empty input (validated by Pydantic)
    - LLM API failure (returns error message)
    """
    try:
        # Get service instances
        text_processor = get_text_processor()
        llm_service = get_llm_service()

        # Extract keywords using local processing
        keywords = text_processor.extract_keywords(request.text)

        # Get LLM analysis
        try:
            llm_result = llm_service.analyze_text(request.text)
        except Exception as e:
            # Handle LLM API failure
            logger.error(f"LLM analysis failed: {str(e)}")
            # Provide fallback values
            llm_result = {
                "summary": "Analysis failed due to LLM error. Text stored for later processing.",
                "title": None,
                "topics": ["error", "processing", "failed"],
                "sentiment": "neutral"
            }

        # Calculate confidence score
        confidence_score = text_processor.calculate_confidence_score(
            request.text,
            llm_result["summary"],
            llm_result["topics"]
        )

        # Create database entry
        analysis = Analysis(
            original_text=request.text,
            summary=llm_result["summary"],
            title=llm_result["title"],
            topics=llm_result["topics"],
            sentiment=llm_result["sentiment"],
            keywords=keywords if keywords else ["none", "found", "extracted"],
            confidence_score=confidence_score
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        return AnalysisResponse.model_validate(analysis)

    except ValueError as e:
        # Handle validation errors (e.g., empty input)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_analyses(
        topic: str = Query(..., min_length=1, description="Topic or keyword to search for"),
        db: Session = Depends(get_db)
):
    """
    Search stored analyses by topic or keyword.
    
    Searches in:
    - Topics (JSON array)
    - Keywords (JSON array)
    - Title
    - Summary
    """
    try:
        # Search in database
        search_term = topic.lower()

        # Get all analyses (since SQLite JSON search is limited)
        all_analyses = db.query(Analysis).all()

        # Filter analyses that match the search term
        matching_analyses = []
        for analysis in all_analyses:
            # Check if search term is in topics
            topics_match = any(search_term in t.lower() for t in analysis.topics)

            # Check if search term is in keywords
            keywords_match = any(search_term in k.lower() for k in analysis.keywords)

            # Check if search term is in title
            title_match = analysis.title and search_term in analysis.title.lower()

            # Check if search term is in summary
            summary_match = search_term in analysis.summary.lower()

            if topics_match or keywords_match or title_match or summary_match:
                matching_analyses.append(analysis)

        # Convert to response models
        analyses_response = [AnalysisResponse.model_validate(a) for a in matching_analyses]

        return SearchResponse(
            analyses=analyses_response,
            total_count=len(analyses_response),
            search_term=topic
        )

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/analyses", response_model=List[AnalysisResponse])
async def get_all_analyses(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Get all analyses with pagination."""
    analyses = db.query(Analysis).offset(skip).limit(limit).all()
    return [AnalysisResponse.model_validate(a) for a in analyses]


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
        analysis_id: int,
        db: Session = Depends(get_db)
):
    """Get a specific analysis by ID."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse.model_validate(analysis)
