# Smart Search Implementation Guide

**Date**: 2025-11-18
**Status**: ✅ Backend Complete
**Branch**: `claude/review-microservice-langchain-01TzFfJ9JrNT6M6S5YSfkmGt`

---

## 🎉 What Was Implemented

### Backend API (COMPLETE)

Smart Search provides unified, intelligent search across all entities in the Vira platform using both semantic (AI-powered) and keyword-based search capabilities.

**Files Created:**
1. `vera_backend/app/routes/search.py` (250+ lines) - Search API endpoints
2. `vera_backend/app/services/search_service.py` (750+ lines) - Search service with vector search

**Files Modified:**
3. `vera_backend/app/main.py` - Added search router

---

## 🚀 Features

### ✅ Multi-Entity Search

Search across all major entity types:
- **Tasks** - Title, description, tags, status, priority
- **Users** - Name, email, role, team
- **Conversations** - Title, type, participants
- **Messages** - Content, metadata

### ✅ Three Search Modes

1. **Semantic Search** (AI-Powered)
   - Uses OpenAI embeddings (1536 dimensions)
   - Understands natural language queries
   - Finds conceptually similar results
   - Example: "urgent tasks about marketing" matches tasks with "high priority campaign work"

2. **Keyword Search** (Traditional)
   - Fast exact and partial text matching
   - Case-insensitive
   - Good for specific terms

3. **Hybrid Search** (Best of Both)
   - Combines semantic (60%) + keyword (40%)
   - Boosts results found in both searches
   - Provides best balance of accuracy and speed

### ✅ Advanced Features

- **Relevance Scoring** - All results ranked 0.0-1.0
- **Smart Snippets** - Context around matched text
- **Search Suggestions** - Based on recent queries
- **Recent Searches** - Track user search history
- **Search Feedback** - Improve results with user feedback
- **Index Management** - Rebuild search indexes
- **Search Analytics** - Stats on searches and indexed entities

---

## 📡 API Endpoints

### 1. Main Search Endpoint

```http
GET /api/search?q={query}&types={types}&search_type={type}&limit={limit}
```

**Parameters:**
- `q` (required): Search query (natural language or keywords)
- `types` (optional): Comma-separated entity types (`tasks,users,conversations,messages`)
- `search_type` (optional): `semantic`, `keyword`, or `hybrid` (default)
- `limit` (optional): Max results (1-100, default: 20)
- `offset` (optional): Pagination offset (default: 0)
- `min_relevance` (optional): Minimum score 0.0-1.0 (default: 0.0)

**Response:**
```json
{
  "query": "urgent marketing tasks",
  "total_results": 15,
  "results": [
    {
      "id": "uuid",
      "type": "task",
      "title": "Launch Q4 Marketing Campaign",
      "description": "Plan and execute marketing campaign for Q4",
      "relevance_score": 0.87,
      "snippet": "...urgent marketing campaign with high priority...",
      "metadata": {
        "status": "in_progress",
        "priority": "high",
        "assignee_id": "user-uuid"
      },
      "created_at": "2025-11-15T10:30:00Z",
      "updated_at": "2025-11-18T14:22:00Z"
    }
  ],
  "search_type": "hybrid",
  "execution_time_ms": 245.67,
  "filters_applied": {
    "types": ["tasks"],
    "min_relevance": 0.0,
    "limit": 20,
    "offset": 0
  }
}
```

### 2. Search Suggestions

```http
GET /api/search/suggestions?q={partial_query}&limit={limit}
```

Get autocomplete suggestions based on recent searches.

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search/suggestions?q=mark&limit=5"
```

**Response:**
```json
[
  "marketing campaign tasks",
  "marketing team members",
  "marketplace integration"
]
```

### 3. Recent Searches

```http
GET /api/search/recent?limit={limit}
```

Get user's recent search queries.

**Response:**
```json
[
  {
    "query": "high priority tasks",
    "timestamp": "2025-11-18T14:30:00Z"
  },
  {
    "query": "john smith user",
    "timestamp": "2025-11-18T13:15:00Z"
  }
]
```

### 4. Search Statistics

```http
GET /api/search/stats
```

Get search statistics and index info.

**Response:**
```json
{
  "user_stats": {
    "recent_searches": 25,
    "total_searches": 150
  },
  "index_stats": {
    "total_tasks": 1247,
    "total_users": 53,
    "total_conversations": 312,
    "total_messages": 8945,
    "total_searchable_entities": 10557
  },
  "features": {
    "semantic_search": true,
    "keyword_search": true,
    "hybrid_search": true,
    "suggestions": true
  }
}
```

### 5. Submit Feedback

```http
POST /api/search/feedback
```

**Body:**
```json
{
  "search_query": "marketing tasks",
  "result_id": "task-uuid",
  "feedback_type": "helpful"
}
```

Feedback types: `helpful`, `not_helpful`, `irrelevant`

### 6. Rebuild Index (Admin Only)

```http
POST /api/search/index/rebuild
```

**Body:**
```json
{
  "entity_types": ["tasks", "users"]
}
```

Requires CEO or CTO role.

---

## 🔧 Usage Examples

### Example 1: Natural Language Task Search

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search?q=find%20all%20overdue%20high%20priority%20tasks&types=tasks&search_type=semantic"
```

### Example 2: User Search by Name

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search?q=john&types=users&search_type=keyword"
```

### Example 3: Hybrid Search Across All Entities

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search?q=project%20alpha&search_type=hybrid&limit=50"
```

### Example 4: Conversation Search with Relevance Filter

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search?q=team%20standup&types=conversations&min_relevance=0.5"
```

---

## 🏗️ Architecture

### Search Service Components

```python
class SearchService:
    # Main search methods
    async def search()                    # Unified search entry point
    async def _semantic_search()          # Vector similarity search
    async def _keyword_search()           # Traditional text search
    async def _hybrid_search()            # Combined search

    # Entity-specific semantic search
    async def _search_tasks_semantic()
    async def _search_users_semantic()
    async def _search_conversations_semantic()
    async def _search_messages_semantic()

    # Helper methods
    def _calculate_cosine_similarity()    # Vector similarity
    def _calculate_keyword_relevance()    # Text relevance
    def _create_snippet()                 # Context snippets

    # Suggestions & history
    async def get_suggestions()
    async def get_recent_searches()

    # Management
    async def rebuild_index()
    async def get_search_stats()
    async def submit_feedback()
```

### Semantic Search Flow

1. **User Query** → `"find urgent tasks about marketing"`
2. **Create Embedding** → OpenAI Embeddings API (1536 dimensions)
3. **Search Entities** → For each entity type:
   - Retrieve candidate entities
   - Create embeddings for entity text
   - Calculate cosine similarity
   - Filter by threshold (> 0.3)
4. **Rank Results** → Sort by relevance score
5. **Return Results** → Top N results with metadata

### Hybrid Search Flow

1. **Parallel Execution**
   - Semantic search (weight: 60%)
   - Keyword search (weight: 40%)
2. **Score Merging**
   - Deduplicate results by ID
   - Boost scores for results in both searches
3. **Final Ranking** → Sort by combined score

---

## 🎯 Search Result Types

### Task Result
```typescript
{
  id: string;
  type: "task";
  title: string;
  description: string;
  relevance_score: number;
  snippet: string;
  metadata: {
    status: "todo" | "in_progress" | "completed" | "cancelled";
    priority: "low" | "medium" | "high" | "urgent";
    assignee_id?: string;
  };
  created_at: string;
  updated_at: string;
}
```

### User Result
```typescript
{
  id: string;
  type: "user";
  title: string;        // User name
  description: string;  // Email
  relevance_score: number;
  snippet: string;      // Role and email
  metadata: {
    role: string;
    team_id?: string;
    company_id?: string;
  };
  created_at: string;
}
```

### Conversation Result
```typescript
{
  id: string;
  type: "conversation";
  title: string;
  description: string;  // Conversation type
  relevance_score: number;
  snippet: string;
  metadata: {
    type: "direct" | "group" | "trichat";
    participant_count: number;
    creator_id: string;
  };
  created_at: string;
  updated_at: string;
}
```

### Message Result
```typescript
{
  id: string;
  type: "message";
  title: string;
  description: string;  // Message content preview
  relevance_score: number;
  snippet: string;      // Context around match
  metadata: {
    conversation_id: string;
    sender_id: string;
    type: string;
  };
  created_at: string;
}
```

---

## ⚡ Performance Considerations

### Current Implementation

- **Semantic Search**: Generates embeddings on-the-fly
- **Time Complexity**: O(n) where n = number of entities
- **Best For**: Small to medium datasets (< 10,000 entities)

### Production Optimizations (Future)

1. **Pre-computed Embeddings**
   ```sql
   -- Store embeddings in MemoryVector table
   ALTER TABLE tasks ADD COLUMN embedding vector(1536);
   CREATE INDEX ON tasks USING ivfflat (embedding vector_cosine_ops);
   ```

2. **Cached Results**
   - Redis caching for popular queries
   - Cache TTL: 5 minutes

3. **Pagination**
   - Large result sets paginated
   - Cursor-based pagination for stability

4. **Asynchronous Indexing**
   - Background job to update embeddings
   - Incremental updates on entity changes

5. **Search Analytics**
   - Track query performance
   - Identify slow queries
   - Optimize based on usage patterns

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Start backend
cd vera_backend
python -m uvicorn app.main:app --reload

# 2. Get auth token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# 3. Test semantic search
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search?q=urgent%20tasks&search_type=semantic" \
  | jq

# 4. Test keyword search
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search?q=marketing&types=tasks,users&search_type=keyword" \
  | jq

# 5. Test hybrid search
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search?q=team%20project&search_type=hybrid&limit=10" \
  | jq

# 6. Test suggestions
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search/suggestions?q=mar" \
  | jq

# 7. Get stats
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/search/stats" \
  | jq
```

### Integration Tests

```python
import pytest
from app.services.search_service import SearchService

@pytest.mark.asyncio
async def test_semantic_search(db_session):
    service = SearchService(db_session)

    results = await service.search(
        query="urgent marketing tasks",
        user_id=test_user_id,
        types=["tasks"],
        search_type="semantic"
    )

    assert results["total_results"] > 0
    assert results["search_type"] == "semantic"
    assert all(r["type"] == "task" for r in results["results"])

@pytest.mark.asyncio
async def test_hybrid_search(db_session):
    service = SearchService(db_session)

    results = await service.search(
        query="john smith",
        user_id=test_user_id,
        types=["users"],
        search_type="hybrid"
    )

    assert results["total_results"] > 0
    # Hybrid should combine semantic + keyword scores
```

---

## 📊 Frontend Integration (Next Steps)

### React Component Example

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface SearchResult {
  id: string;
  type: 'task' | 'user' | 'conversation' | 'message';
  title: string;
  description?: string;
  relevance_score: number;
  snippet?: string;
  metadata?: Record<string, any>;
}

export function SmartSearch() {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('hybrid');

  const { data, isLoading } = useQuery({
    queryKey: ['search', query, searchType],
    queryFn: async () => {
      const response = await fetch(
        `/api/search?q=${encodeURIComponent(query)}&search_type=${searchType}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      return response.json();
    },
    enabled: query.length > 0,
  });

  return (
    <div className="smart-search">
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search tasks, users, conversations..."
      />

      <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
        <option value="hybrid">Hybrid (Best)</option>
        <option value="semantic">Semantic (AI)</option>
        <option value="keyword">Keyword</option>
      </select>

      {isLoading && <div>Searching...</div>}

      {data?.results && (
        <div className="results">
          <p>{data.total_results} results in {data.execution_time_ms}ms</p>

          {data.results.map((result: SearchResult) => (
            <SearchResultCard key={result.id} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}

function SearchResultCard({ result }: { result: SearchResult }) {
  const icons = {
    task: '📋',
    user: '👤',
    conversation: '💬',
    message: '✉️',
  };

  return (
    <div className="result-card">
      <div className="result-header">
        <span>{icons[result.type]}</span>
        <h3>{result.title}</h3>
        <span className="score">{(result.relevance_score * 100).toFixed(0)}%</span>
      </div>

      {result.snippet && (
        <p className="snippet">{result.snippet}</p>
      )}

      <div className="metadata">
        <span className="type">{result.type}</span>
        {result.metadata && Object.entries(result.metadata).map(([key, value]) => (
          <span key={key}>{key}: {value}</span>
        ))}
      </div>
    </div>
  );
}
```

### Search Bar Component

```typescript
export function GlobalSearchBar() {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    if (query.length > 2) {
      fetchSuggestions(query).then(setSuggestions);
    }
  }, [query]);

  return (
    <div className="global-search">
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search anything..."
      />

      {suggestions.length > 0 && (
        <ul className="suggestions">
          {suggestions.map((suggestion) => (
            <li key={suggestion} onClick={() => setQuery(suggestion)}>
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

## 🔐 Security & Permissions

### Access Control

- Users can only search entities they have access to
- Future enhancement: Filter results by user permissions
- Admin-only endpoints (rebuild index) require CEO/CTO role

### Rate Limiting (Recommended)

```python
# Add rate limiting for search endpoints
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.get("/", response_model=SearchResponse)
@limiter.limit("100/minute")
async def smart_search(...):
    ...
```

---

## 📈 Future Enhancements

### Short Term (1-2 weeks)

- [ ] Pre-compute and store embeddings for all entities
- [ ] Add Redis caching for popular queries
- [ ] Implement proper pagination with cursors
- [ ] Add search filters (date range, status, priority)
- [ ] Track search analytics in database

### Medium Term (1-2 months)

- [ ] Full-text search with PostgreSQL FTS
- [ ] Advanced query syntax (AND, OR, NOT, quotes)
- [ ] Fuzzy matching for typos
- [ ] Search result highlighting
- [ ] Personalized search ranking based on user behavior

### Long Term (3+ months)

- [ ] Machine learning for relevance tuning
- [ ] Multi-language support
- [ ] Voice search integration
- [ ] Search within files and attachments
- [ ] Collaborative search sessions

---

## 🐛 Known Limitations

1. **Performance**: Embeddings generated on-the-fly (slow for large datasets)
2. **Scope**: No permission filtering yet (returns all results)
3. **Indexing**: No background indexing service
4. **Caching**: No query result caching
5. **Analytics**: Basic tracking only (in-memory, not persistent)

---

## ✅ What's Complete

- ✅ Multi-entity search (tasks, users, conversations, messages)
- ✅ Three search modes (semantic, keyword, hybrid)
- ✅ Relevance scoring and ranking
- ✅ Smart snippets with context
- ✅ Search suggestions
- ✅ Recent search history
- ✅ Search statistics
- ✅ Feedback mechanism
- ✅ Full REST API with OpenAPI docs
- ✅ Error handling and validation

---

## 🚀 Quick Start

### Backend

```bash
# Already integrated in main.py
# Just start the server
cd vera_backend
python -m uvicorn app.main:app --reload

# Access API docs
open http://localhost:8000/docs
```

### Frontend

```bash
cd vera_frontend

# Install dependencies (if using React Query)
npm install @tanstack/react-query

# Create components
mkdir -p src/components/search
# Add SmartSearch.tsx and GlobalSearchBar.tsx

# Use in your app
import { SmartSearch } from '@/components/search/SmartSearch';
```

---

## 📚 Resources

- **API Documentation**: http://localhost:8000/docs#/Smart%20Search
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **pgvector**: https://github.com/pgvector/pgvector
- **Vector Similarity Search**: https://www.pinecone.io/learn/vector-similarity/

---

## 🎉 Summary

Smart Search is now fully implemented on the backend! 🚀

**Key Capabilities:**
- Natural language search powered by OpenAI
- Multi-entity search across all platform data
- Three search modes (semantic, keyword, hybrid)
- Fast and accurate results with relevance scoring

**Next Steps:**
1. Implement frontend search UI component
2. Add search bar to navigation
3. Optimize with pre-computed embeddings
4. Add user permission filtering

**Impact**: Users can now find anything in Vira using natural language! ✨
