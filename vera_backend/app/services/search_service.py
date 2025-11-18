"""
Smart Search Service - Unified search across all entities with semantic vector search
"""
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AIServiceError, ViraException
from app.models.sql_models import (
    Company,
    Conversation,
    Message,
    Task,
    User,
    MemoryVector,
)
from app.services.ai_orchestration_service import AIOrchestrationService
from app.services.base import BaseService


class SearchResultType(str, Enum):
    """Types of entities that can be returned in search results"""

    TASK = "task"
    USER = "user"
    CONVERSATION = "conversation"
    MESSAGE = "message"
    FILE = "file"


class SearchService(BaseService):
    """Service for unified smart search across all entities"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.ai_service = AIOrchestrationService(db)
        self.recent_searches = {}  # In-memory cache for recent searches

    async def search(
        self,
        query: str,
        user_id: UUID,
        types: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
        search_type: str = "hybrid",
        min_relevance: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Perform unified search across all entities

        Args:
            query: Search query (natural language or keywords)
            user_id: ID of user performing search
            types: List of entity types to search (tasks, users, conversations, messages)
            limit: Maximum number of results
            offset: Number of results to skip
            search_type: "semantic", "keyword", or "hybrid"
            min_relevance: Minimum relevance score (0.0-1.0)

        Returns:
            Dict containing search results and metadata
        """
        start_time = time.time()

        try:
            # Default to all types if not specified
            if not types:
                types = ["tasks", "users", "conversations", "messages"]

            # Normalize types
            types = [t.lower() for t in types]

            # Store search query for suggestions
            await self._store_search_query(user_id, query)

            # Perform search based on type
            if search_type == "semantic":
                results = await self._semantic_search(query, user_id, types, limit + offset)
            elif search_type == "keyword":
                results = await self._keyword_search(query, user_id, types, limit + offset)
            else:  # hybrid
                results = await self._hybrid_search(query, user_id, types, limit + offset)

            # Filter by minimum relevance
            results = [r for r in results if r["relevance_score"] >= min_relevance]

            # Apply pagination
            total_results = len(results)
            results = results[offset : offset + limit]

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            return {
                "query": query,
                "total_results": total_results,
                "results": results,
                "search_type": search_type,
                "execution_time_ms": round(execution_time_ms, 2),
                "filters_applied": {
                    "types": types,
                    "min_relevance": min_relevance,
                    "limit": limit,
                    "offset": offset,
                },
            }

        except Exception as e:
            raise AIServiceError(f"Search failed: {str(e)}")

    async def _semantic_search(
        self, query: str, user_id: UUID, types: List[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector search using embeddings"""

        try:
            # Create query embedding
            query_embedding = await self.ai_service.create_embeddings([query])
            query_vector = query_embedding[0]

            results = []

            # Search tasks
            if "tasks" in types:
                task_results = await self._search_tasks_semantic(
                    query_vector, user_id, limit
                )
                results.extend(task_results)

            # Search users
            if "users" in types:
                user_results = await self._search_users_semantic(query_vector, user_id, limit)
                results.extend(user_results)

            # Search conversations
            if "conversations" in types:
                conv_results = await self._search_conversations_semantic(
                    query_vector, user_id, limit
                )
                results.extend(conv_results)

            # Search messages
            if "messages" in types:
                message_results = await self._search_messages_semantic(
                    query_vector, user_id, limit
                )
                results.extend(message_results)

            # Sort by relevance score
            results.sort(key=lambda x: x["relevance_score"], reverse=True)

            return results[:limit]

        except Exception as e:
            raise AIServiceError(f"Semantic search failed: {str(e)}")

    async def _keyword_search(
        self, query: str, user_id: UUID, types: List[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Perform traditional keyword-based search"""

        results = []
        query_lower = query.lower()

        # Search tasks
        if "tasks" in types:
            tasks = (
                self.db.query(Task)
                .filter(
                    or_(
                        func.lower(Task.title).contains(query_lower),
                        func.lower(Task.description).contains(query_lower),
                    )
                )
                .limit(limit)
                .all()
            )

            for task in tasks:
                # Calculate keyword relevance
                relevance = self._calculate_keyword_relevance(
                    query_lower, [task.title, task.description or ""]
                )

                results.append(
                    {
                        "id": str(task.id),
                        "type": SearchResultType.TASK,
                        "title": task.title,
                        "description": task.description,
                        "relevance_score": relevance,
                        "snippet": self._create_snippet(task.description or task.title, query),
                        "metadata": {
                            "status": task.status,
                            "priority": task.priority,
                            "assignee_id": str(task.assignee_id) if task.assignee_id else None,
                        },
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    }
                )

        # Search users
        if "users" in types:
            users = (
                self.db.query(User)
                .filter(
                    or_(
                        func.lower(User.name).contains(query_lower),
                        func.lower(User.email).contains(query_lower),
                    )
                )
                .limit(limit)
                .all()
            )

            for user in users:
                relevance = self._calculate_keyword_relevance(
                    query_lower, [user.name, user.email]
                )

                results.append(
                    {
                        "id": str(user.id),
                        "type": SearchResultType.USER,
                        "title": user.name,
                        "description": user.email,
                        "relevance_score": relevance,
                        "snippet": f"{user.role} - {user.email}",
                        "metadata": {
                            "role": user.role,
                            "team_id": str(user.team_id) if user.team_id else None,
                            "company_id": str(user.company_id) if user.company_id else None,
                        },
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": None,
                    }
                )

        # Search conversations
        if "conversations" in types:
            conversations = (
                self.db.query(Conversation)
                .filter(func.lower(Conversation.title).contains(query_lower))
                .limit(limit)
                .all()
            )

            for conv in conversations:
                relevance = self._calculate_keyword_relevance(query_lower, [conv.title])

                results.append(
                    {
                        "id": str(conv.id),
                        "type": SearchResultType.CONVERSATION,
                        "title": conv.title,
                        "description": f"{conv.type.capitalize()} conversation",
                        "relevance_score": relevance,
                        "snippet": conv.title,
                        "metadata": {
                            "type": conv.type,
                            "participant_count": len(conv.participants or []),
                            "creator_id": str(conv.creator_id),
                        },
                        "created_at": conv.created_at.isoformat() if conv.created_at else None,
                        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    }
                )

        # Search messages
        if "messages" in types:
            messages = (
                self.db.query(Message)
                .filter(func.lower(Message.content).contains(query_lower))
                .limit(limit)
                .all()
            )

            for message in messages:
                relevance = self._calculate_keyword_relevance(query_lower, [message.content])

                results.append(
                    {
                        "id": str(message.id),
                        "type": SearchResultType.MESSAGE,
                        "title": f"Message from conversation",
                        "description": message.content[:200],
                        "relevance_score": relevance,
                        "snippet": self._create_snippet(message.content, query),
                        "metadata": {
                            "conversation_id": str(message.conversation_id),
                            "sender_id": str(message.sender_id),
                            "type": message.type,
                        },
                        "created_at": message.timestamp.isoformat() if message.timestamp else None,
                        "updated_at": None,
                    }
                )

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results[:limit]

    async def _hybrid_search(
        self, query: str, user_id: UUID, types: List[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Combine semantic and keyword search with weighted scoring"""

        # Perform both searches
        semantic_results = await self._semantic_search(query, user_id, types, limit)
        keyword_results = await self._keyword_search(query, user_id, types, limit)

        # Merge results with weighted scoring
        merged_results = {}

        # Add semantic results with 60% weight
        for result in semantic_results:
            result_id = result["id"]
            merged_results[result_id] = result.copy()
            merged_results[result_id]["relevance_score"] *= 0.6

        # Add keyword results with 40% weight, or boost if already exists
        for result in keyword_results:
            result_id = result["id"]
            if result_id in merged_results:
                # Boost score if found in both searches
                merged_results[result_id]["relevance_score"] += result["relevance_score"] * 0.4
            else:
                merged_results[result_id] = result.copy()
                merged_results[result_id]["relevance_score"] *= 0.4

        # Convert back to list and sort
        final_results = list(merged_results.values())
        final_results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return final_results[:limit]

    async def _search_tasks_semantic(
        self, query_vector: List[float], user_id: UUID, limit: int
    ) -> List[Dict[str, Any]]:
        """Search tasks using vector similarity"""

        # Note: This requires tasks to have embeddings stored in MemoryVector
        # For now, we'll use a simplified approach

        tasks = self.db.query(Task).limit(limit * 2).all()

        results = []
        for task in tasks:
            # Create text representation for embedding
            task_text = f"{task.title} {task.description or ''}"

            # For production, we'd store embeddings in advance
            # For now, calculate on-the-fly (slower but functional)
            task_embedding = await self.ai_service.create_embeddings([task_text])
            similarity = self._calculate_cosine_similarity(query_vector, task_embedding[0])

            if similarity > 0.3:  # Threshold for relevance
                results.append(
                    {
                        "id": str(task.id),
                        "type": SearchResultType.TASK,
                        "title": task.title,
                        "description": task.description,
                        "relevance_score": similarity,
                        "snippet": task.description[:200] if task.description else task.title,
                        "metadata": {
                            "status": task.status,
                            "priority": task.priority,
                            "assignee_id": str(task.assignee_id) if task.assignee_id else None,
                        },
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    }
                )

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]

    async def _search_users_semantic(
        self, query_vector: List[float], user_id: UUID, limit: int
    ) -> List[Dict[str, Any]]:
        """Search users using vector similarity"""

        users = self.db.query(User).limit(limit * 2).all()

        results = []
        for user in users:
            user_text = f"{user.name} {user.email} {user.role}"

            user_embedding = await self.ai_service.create_embeddings([user_text])
            similarity = self._calculate_cosine_similarity(query_vector, user_embedding[0])

            if similarity > 0.3:
                results.append(
                    {
                        "id": str(user.id),
                        "type": SearchResultType.USER,
                        "title": user.name,
                        "description": user.email,
                        "relevance_score": similarity,
                        "snippet": f"{user.role} - {user.email}",
                        "metadata": {
                            "role": user.role,
                            "team_id": str(user.team_id) if user.team_id else None,
                        },
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": None,
                    }
                )

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]

    async def _search_conversations_semantic(
        self, query_vector: List[float], user_id: UUID, limit: int
    ) -> List[Dict[str, Any]]:
        """Search conversations using vector similarity"""

        conversations = self.db.query(Conversation).limit(limit * 2).all()

        results = []
        for conv in conversations:
            conv_text = f"{conv.title} {conv.type}"

            conv_embedding = await self.ai_service.create_embeddings([conv_text])
            similarity = self._calculate_cosine_similarity(query_vector, conv_embedding[0])

            if similarity > 0.3:
                results.append(
                    {
                        "id": str(conv.id),
                        "type": SearchResultType.CONVERSATION,
                        "title": conv.title,
                        "description": f"{conv.type.capitalize()} conversation",
                        "relevance_score": similarity,
                        "snippet": conv.title,
                        "metadata": {
                            "type": conv.type,
                            "participant_count": len(conv.participants or []),
                        },
                        "created_at": conv.created_at.isoformat() if conv.created_at else None,
                        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    }
                )

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]

    async def _search_messages_semantic(
        self, query_vector: List[float], user_id: UUID, limit: int
    ) -> List[Dict[str, Any]]:
        """Search messages using vector similarity"""

        messages = self.db.query(Message).limit(limit * 2).all()

        results = []
        for message in messages:
            message_embedding = await self.ai_service.create_embeddings([message.content])
            similarity = self._calculate_cosine_similarity(query_vector, message_embedding[0])

            if similarity > 0.3:
                results.append(
                    {
                        "id": str(message.id),
                        "type": SearchResultType.MESSAGE,
                        "title": "Message",
                        "description": message.content[:200],
                        "relevance_score": similarity,
                        "snippet": self._create_snippet(message.content, ""),
                        "metadata": {
                            "conversation_id": str(message.conversation_id),
                            "sender_id": str(message.sender_id),
                        },
                        "created_at": message.timestamp.isoformat() if message.timestamp else None,
                        "updated_at": None,
                    }
                )

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]

    def _calculate_cosine_similarity(
        self, vec1: List[float], vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np

        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _calculate_keyword_relevance(self, query: str, fields: List[str]) -> float:
        """Calculate keyword relevance score"""

        query_words = set(query.lower().split())
        if not query_words:
            return 0.0

        total_matches = 0
        total_words = 0

        for field in fields:
            if field:
                field_words = set(field.lower().split())
                matches = len(query_words.intersection(field_words))
                total_matches += matches
                total_words += len(field_words)

        if total_words == 0:
            return 0.0

        # Calculate relevance as match ratio with boost for exact matches
        match_ratio = total_matches / len(query_words)
        coverage_ratio = total_matches / total_words if total_words > 0 else 0

        return min(1.0, (match_ratio * 0.7 + coverage_ratio * 0.3))

    def _create_snippet(self, text: str, query: str, context_chars: int = 100) -> str:
        """Create a snippet with context around the query match"""

        if not text or not query:
            return text[:200] if text else ""

        query_lower = query.lower()
        text_lower = text.lower()

        # Find query position
        pos = text_lower.find(query_lower)

        if pos == -1:
            # Query not found, return beginning
            return text[:200] + ("..." if len(text) > 200 else "")

        # Calculate snippet bounds
        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(query) + context_chars)

        snippet = text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    async def get_suggestions(
        self, partial_query: str, user_id: UUID, limit: int = 10
    ) -> List[str]:
        """Get search suggestions based on partial query"""

        suggestions = []

        # Get recent searches matching partial query
        if str(user_id) in self.recent_searches:
            user_searches = self.recent_searches[str(user_id)]
            matching = [
                s for s in user_searches if partial_query.lower() in s.lower()
            ]
            suggestions.extend(matching[:limit])

        # Could add more sophisticated suggestions here
        # e.g., popular searches, entity name autocomplete, etc.

        return suggestions[:limit]

    async def get_recent_searches(
        self, user_id: UUID, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's recent search queries"""

        if str(user_id) not in self.recent_searches:
            return []

        recent = self.recent_searches[str(user_id)][:limit]

        return [{"query": q, "timestamp": datetime.utcnow().isoformat()} for q in recent]

    async def _store_search_query(self, user_id: UUID, query: str) -> None:
        """Store search query for suggestions"""

        user_id_str = str(user_id)

        if user_id_str not in self.recent_searches:
            self.recent_searches[user_id_str] = []

        # Add to beginning of list
        if query not in self.recent_searches[user_id_str]:
            self.recent_searches[user_id_str].insert(0, query)

        # Keep only last 50 searches
        self.recent_searches[user_id_str] = self.recent_searches[user_id_str][:50]

    async def rebuild_index(
        self, entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Rebuild search index (for future implementation)"""

        # This would rebuild vector embeddings for all entities
        # For now, return a placeholder

        return {
            "entity_types": entity_types or ["tasks", "users", "conversations", "messages"],
            "estimated_time": "5-10 minutes",
            "status": "not_implemented",
            "note": "Index rebuilding will be implemented in future version",
        }

    async def get_search_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get search statistics"""

        recent_count = (
            len(self.recent_searches.get(str(user_id), [])) if str(user_id) in self.recent_searches else 0
        )

        # Get entity counts
        task_count = self.db.query(Task).count()
        user_count = self.db.query(User).count()
        conversation_count = self.db.query(Conversation).count()
        message_count = self.db.query(Message).count()

        return {
            "user_stats": {
                "recent_searches": recent_count,
                "total_searches": recent_count,  # Would track this properly in production
            },
            "index_stats": {
                "total_tasks": task_count,
                "total_users": user_count,
                "total_conversations": conversation_count,
                "total_messages": message_count,
                "total_searchable_entities": task_count
                + user_count
                + conversation_count
                + message_count,
            },
            "features": {
                "semantic_search": True,
                "keyword_search": True,
                "hybrid_search": True,
                "suggestions": True,
            },
        }

    async def submit_feedback(
        self, user_id: UUID, query: str, result_id: str, feedback_type: str
    ) -> None:
        """Submit feedback on search results (for future ML improvements)"""

        # In production, this would store feedback for improving search relevance
        # For now, just validate inputs

        valid_feedback_types = ["helpful", "not_helpful", "irrelevant"]
        if feedback_type not in valid_feedback_types:
            raise ViraException(
                f"Invalid feedback type. Must be one of: {', '.join(valid_feedback_types)}"
            )

        # Would store in database for ML training
        pass
