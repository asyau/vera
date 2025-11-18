"""
Smart Search Routes - Natural Language Search Across All Entities
Implements semantic vector search and keyword-based search across tasks, users, conversations, and files
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.core.exceptions import ViraException
from app.database import get_db
from app.services.search_service import SearchService, SearchResultType

router = APIRouter()


# Response Models
class SearchResult(BaseModel):
    """Individual search result"""

    id: str
    type: SearchResultType
    title: str
    description: Optional[str] = None
    relevance_score: float
    snippet: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class SearchResponse(BaseModel):
    """Search response with results and metadata"""

    query: str
    total_results: int
    results: List[SearchResult]
    search_type: str  # "semantic" or "keyword" or "hybrid"
    execution_time_ms: float
    filters_applied: Dict[str, Any]


class SearchFilters(BaseModel):
    """Filters for search requests"""

    types: Optional[List[str]] = None
    user_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


# Routes
@router.get("/", response_model=SearchResponse)
async def smart_search(
    q: str = Query(..., min_length=1, description="Search query (natural language or keywords)"),
    types: Optional[str] = Query(
        None,
        description="Comma-separated entity types to search: tasks,users,conversations,messages",
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    search_type: str = Query(
        "hybrid",
        description="Search type: semantic (vector), keyword, or hybrid (both)",
    ),
    min_relevance: float = Query(
        0.0, ge=0.0, le=1.0, description="Minimum relevance score (0.0-1.0)"
    ),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Smart search across all entities using natural language or keywords.

    Examples:
    - "Find all high priority tasks assigned to John"
    - "Show me conversations about the marketing project"
    - "Search for users in the engineering team"
    - "Find messages containing 'deadline'"
    """
    try:
        search_service = SearchService(db)

        # Parse types filter
        types_list = None
        if types:
            types_list = [t.strip() for t in types.split(",")]

        # Perform search
        search_results = await search_service.search(
            query=q,
            user_id=UUID(current_user_id),
            types=types_list,
            limit=limit,
            offset=offset,
            search_type=search_type,
            min_relevance=min_relevance,
        )

        return search_results

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get search suggestions based on partial query.
    Returns recent searches and relevant suggestions.
    """
    try:
        search_service = SearchService(db)

        suggestions = await search_service.get_suggestions(
            partial_query=q, user_id=UUID(current_user_id), limit=limit
        )

        return suggestions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_searches(
    limit: int = Query(10, ge=1, le=50, description="Number of recent searches to return"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's recent search queries"""
    try:
        search_service = SearchService(db)

        recent_searches = await search_service.get_recent_searches(
            user_id=UUID(current_user_id), limit=limit
        )

        return recent_searches

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent searches: {str(e)}"
        )


@router.post("/index/rebuild")
async def rebuild_search_index(
    entity_types: Optional[List[str]] = None,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Rebuild search index for specific entity types.
    Requires admin privileges.
    """
    try:
        from app.models.sql_models import User

        # Check if user has admin privileges
        user = db.query(User).filter(User.id == UUID(current_user_id)).first()
        if not user or user.role not in ["CEO", "CTO"]:
            raise HTTPException(
                status_code=403, detail="Admin privileges required to rebuild search index"
            )

        search_service = SearchService(db)

        result = await search_service.rebuild_index(entity_types=entity_types)

        return {
            "message": "Search index rebuild initiated",
            "entity_types": result.get("entity_types"),
            "estimated_time": result.get("estimated_time"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {str(e)}")


@router.get("/stats")
async def get_search_stats(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get search statistics and index information"""
    try:
        search_service = SearchService(db)

        stats = await search_service.get_search_stats(user_id=UUID(current_user_id))

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search stats: {str(e)}")


@router.post("/feedback")
async def submit_search_feedback(
    search_query: str,
    result_id: str,
    feedback_type: str = Query(..., description="helpful, not_helpful, or irrelevant"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Submit feedback on search results to improve relevance.
    Helps train the search algorithm.
    """
    try:
        search_service = SearchService(db)

        await search_service.submit_feedback(
            user_id=UUID(current_user_id),
            query=search_query,
            result_id=result_id,
            feedback_type=feedback_type,
        )

        return {"message": "Feedback submitted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")
