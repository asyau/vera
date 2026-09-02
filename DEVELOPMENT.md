# Development Guide

## 🛠️ Development Workflow

This guide covers the development workflow, code structure, and best practices for the Vira AI platform.

---

## 📁 Project Structure

### Backend Structure (`vera_backend/`)

```
vera_backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── config.py              # Settings and environment variables
│   │   ├── api_gateway.py         # API Gateway with CORS, auth middleware
│   │   └── exceptions.py          # Custom exception classes
│   ├── models/
│   │   ├── sql_models.py          # SQLAlchemy ORM models
│   │   └── pydantic_models.py     # Pydantic schemas for validation
│   ├── routes/
│   │   ├── simple_auth.py         # Authentication endpoints
│   │   ├── task.py                # Task management
│   │   ├── messaging.py           # Messaging endpoints
│   │   ├── search.py              # Smart search
│   │   ├── org_hierarchy.py       # Org graph
│   │   ├── voice.py               # Voice STT/TTS (NEW)
│   │   ├── team.py                # Team management
│   │   ├── user.py                # User management
│   │   ├── conversation.py        # Conversations
│   │   ├── websocket.py           # WebSocket/Socket.IO
│   │   ├── integrations.py        # Third-party integrations
│   │   ├── langgraph_routes.py    # LangGraph workflows
│   │   └── openai_service.py      # AI orchestration
│   ├── services/
│   │   ├── base.py                # Base service class
│   │   ├── communication_service.py  # Messaging logic
│   │   ├── notification_service.py   # Multi-channel notifications
│   │   ├── file_service.py        # File processing
│   │   ├── websocket_service.py   # WebSocket management
│   │   └── voice/                 # Voice services (NEW)
│   │       ├── __init__.py
│   │       └── voice_service.py   # STT/TTS implementations
│   ├── repositories/
│   │   ├── user_repository.py     # User data access
│   │   └── task_repository.py     # Task data access
│   └── database.py                # Database session management
├── requirements.txt               # Production dependencies
├── requirements.dev.txt           # Development dependencies
└── .env.example                   # Environment variable template
```

### Frontend Structure (`vera_frontend/`)

```
vera_frontend/
├── src/
│   ├── App.tsx                    # Root component with routing
│   ├── main.tsx                   # Application entry point
│   ├── components/
│   │   ├── ui/                    # Shadcn UI components
│   │   ├── auth/                  # Authentication components
│   │   ├── chat/                  # Chat components
│   │   ├── tasks/                 # Task components
│   │   ├── layout/
│   │   │   └── Navbar.tsx         # Navigation with search
│   │   ├── briefing/              # Daily briefing
│   │   ├── search/                # Smart search (NEW)
│   │   │   └── SmartSearch.tsx
│   │   └── org/                   # Org hierarchy (NEW)
│   │       ├── OrgHierarchyGraph.tsx
│   │       └── nodes/
│   │           └── OrgNode.tsx
│   ├── pages/
│   │   ├── Index.tsx              # Dashboard
│   │   ├── Tasks.tsx              # Task management
│   │   ├── Login.tsx              # Login page
│   │   ├── Signup.tsx             # Registration
│   │   ├── Profile.tsx            # User profile
│   │   ├── Teams.tsx              # Team management
│   │   ├── OrgHierarchy.tsx       # Org graph page (NEW)
│   │   └── ...
│   ├── stores/
│   │   ├── authStore.ts           # Authentication state
│   │   ├── chatStore.ts           # Chat/messaging state
│   │   ├── taskStore.ts           # Task state
│   │   └── teamStore.ts           # Team state
│   ├── services/
│   │   ├── api.ts                 # API client with all endpoints
│   │   └── websocketService.ts    # WebSocket client
│   ├── types/
│   │   ├── chat.ts                # Chat type definitions
│   │   ├── task.ts                # Task type definitions
│   │   ├── search.ts              # Search types (NEW)
│   │   └── org.ts                 # Org hierarchy types (NEW)
│   └── lib/
│       └── utils.ts               # Utility functions
├── package.json                   # Node dependencies
└── vite.config.ts                 # Vite configuration
```

---

## 🔧 Development Setup

### 1. Install Development Dependencies

**Backend**:
```bash
cd vera_backend
pip install -r requirements.txt
pip install -r requirements.dev.txt  # pytest, black, flake8, etc.
```

**Frontend**:
```bash
cd vera_frontend
npm install
```

### 2. Set Up Pre-commit Hooks (Recommended)

```bash
# Backend
cd vera_backend
pip install pre-commit
pre-commit install

# Frontend - uses built-in ESLint/Prettier
cd vera_frontend
npm run lint  # Check linting
npm run format  # Format code
```

### 3. Database Development

```bash
# Create development database
createdb vira_dev

# Set DATABASE_URL in .env
DATABASE_URL=postgresql://localhost/vira_dev

# Run migrations (if using Alembic)
alembic upgrade head
```

### 4. Environment Variables

Create separate `.env` files for different environments:

```bash
# Development
cp .env.example .env.development

# Testing
cp .env.example .env.test

# Production
cp .env.example .env.production
```

---

## 🧪 Testing

### Backend Tests

```bash
cd vera_backend

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_voice_service.py

# Run specific test
pytest tests/test_voice_service.py::test_openai_stt
```

### Frontend Tests

```bash
cd vera_frontend

# Run unit tests
npm test

# Run with coverage
npm test -- --coverage

# Run E2E tests (if configured)
npm run test:e2e
```

### API Testing

```bash
# Using curl
curl -X POST http://localhost:8000/api/voice/tts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Test","voice":"alloy"}'

# Using Python requests
python scripts/test_api.py

# Using Postman
# Import collection from docs/postman_collection.json
```

---

## 🎨 Code Style & Standards

### Backend (Python)

**Formatting**: Black
```bash
black app/
```

**Linting**: Flake8
```bash
flake8 app/
```

**Type Checking**: MyPy (optional)
```bash
mypy app/
```

**Standards**:
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Maximum line length: 100 characters
- Use async/await for I/O operations

**Example**:
```python
async def create_user(
    self,
    email: str,
    password: str,
    name: str,
    role: str = "employee"
) -> User:
    """
    Create a new user account.

    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        name: User's full name
        role: User role (employee/supervisor/admin)

    Returns:
        User: Created user object

    Raises:
        ValidationError: If email already exists
    """
    # Implementation
```

### Frontend (TypeScript/React)

**Formatting**: Prettier
```bash
npm run format
```

**Linting**: ESLint
```bash
npm run lint
```

**Standards**:
- Use TypeScript for type safety
- Prefer functional components with hooks
- Use Zustand for global state
- Follow React best practices
- Use meaningful variable names

**Example**:
```typescript
interface SmartSearchProps {
  onResultClick?: (result: SearchResult) => void;
  autoFocus?: boolean;
  placeholder?: string;
  className?: string;
}

export function SmartSearch({
  onResultClick,
  autoFocus = false,
  placeholder = 'Search...',
  className,
}: SmartSearchProps) {
  // Component implementation
}
```

---

## 🚀 Adding New Features

### 1. Backend API Endpoint

**Step 1**: Define Pydantic model
```python
# app/models/pydantic_models.py
class FeatureRequest(BaseModel):
    name: str
    description: str
    priority: str = "medium"
```

**Step 2**: Create route
```python
# app/routes/feature.py
from fastapi import APIRouter, Depends
from app.core.api_gateway import AuthenticationMiddleware

router = APIRouter()

@router.post("/features")
async def create_feature(
    request: FeatureRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db)
):
    # Implementation
    return {"status": "success"}
```

**Step 3**: Register router
```python
# app/main.py
from app.routes import feature

app.include_router(
    feature.router,
    prefix="/api/features",
    tags=["Features"]
)
```

### 2. Frontend Component

**Step 1**: Create types
```typescript
// src/types/feature.ts
export interface Feature {
  id: string;
  name: string;
  description: string;
  priority: string;
}
```

**Step 2**: Add API method
```typescript
// src/services/api.ts
async createFeature(data: FeatureRequest): Promise<Feature> {
  return this.request<Feature>({
    method: 'POST',
    url: '/api/features',
    data,
  });
}
```

**Step 3**: Create component
```typescript
// src/components/features/FeatureList.tsx
export function FeatureList() {
  const [features, setFeatures] = useState<Feature[]>([]);

  useEffect(() => {
    api.getFeatures().then(setFeatures);
  }, []);

  return (
    <div>
      {features.map(feature => (
        <FeatureCard key={feature.id} feature={feature} />
      ))}
    </div>
  );
}
```

### 3. Database Model

```python
# app/models/sql_models.py
class Feature(Base):
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

## 🔌 Adding Integrations

### Example: Add a new notification channel

**Step 1**: Add configuration
```python
# app/core/config.py
telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
```

**Step 2**: Implement service method
```python
# app/services/notification_service.py
async def _send_telegram_notification(
    self,
    recipient: User,
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Send Telegram notification"""

    if not settings.telegram_bot_token:
        return {
            "channel": "telegram",
            "status": "skipped",
            "reason": "Telegram not configured",
        }

    try:
        import requests

        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        data = {
            "chat_id": recipient.telegram_id,
            "text": f"**{title}**\n\n{content}",
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()

        return {"channel": "telegram", "status": "sent"}

    except Exception as e:
        raise ExternalServiceError(f"Telegram notification failed: {str(e)}")
```

**Step 3**: Update notification channel enum
```python
class NotificationChannel(Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    PUSH = "push"
    TELEGRAM = "telegram"  # NEW
```

**Step 4**: Update .env.example
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token
```

---

## 📊 Performance Optimization

### Backend

**1. Database Query Optimization**
```python
# Bad - N+1 queries
users = db.query(User).all()
for user in users:
    tasks = user.tasks  # Lazy loading

# Good - Eager loading
users = db.query(User).options(joinedload(User.tasks)).all()
```

**2. Response Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_static_data():
    # Expensive operation
    return data
```

**3. Async Operations**
```python
# Good - concurrent requests
async def fetch_all_data():
    results = await asyncio.gather(
        fetch_users(),
        fetch_tasks(),
        fetch_teams()
    )
    return results
```

### Frontend

**1. Code Splitting**
```typescript
// Lazy load routes
const OrgHierarchy = lazy(() => import('./pages/OrgHierarchy'));

<Route path="/org-hierarchy" element={
  <Suspense fallback={<Loading />}>
    <OrgHierarchy />
  </Suspense>
} />
```

**2. Memoization**
```typescript
const MemoizedComponent = memo(function Component({ data }) {
  // Expensive rendering
  return <div>{/* ... */}</div>;
});
```

**3. Debouncing**
```typescript
const debouncedSearch = useDebouncedCallback(
  (query: string) => {
    performSearch(query);
  },
  300
);
```

---

## 🔒 Security Best Practices

### 1. Input Validation

**Backend**:
```python
from pydantic import EmailStr, constr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=100)
    name: constr(min_length=1, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

**Frontend**:
```typescript
const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(100),
});
```

### 2. SQL Injection Prevention

```python
# Good - parameterized queries (SQLAlchemy handles this)
users = db.query(User).filter(User.email == email).all()

# Bad - never do this
db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### 3. XSS Prevention

```typescript
// React automatically escapes by default
<div>{userInput}</div>  // Safe

// Use dangerouslySetInnerHTML only when necessary
<div dangerouslySetInnerHTML={{ __html: sanitizedHTML }} />
```

### 4. Authentication

```python
# Always check authentication
@router.get("/protected")
async def protected_route(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id)
):
    # User is authenticated
    pass
```

---

## 🐛 Debugging

### Backend Debugging

**1. Enable debug logging**
```python
# app/main.py
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**2. Use debugger**
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger
# Create .vscode/launch.json
```

**3. Profile performance**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Code to profile
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Frontend Debugging

**1. React DevTools**
- Install browser extension
- Inspect component tree
- View props and state

**2. Network Tab**
- Monitor API calls
- Check request/response
- Identify slow requests

**3. Console Debugging**
```typescript
// Structured logging
console.log('User data:', { userId, name, email });

// Performance timing
console.time('search');
await performSearch();
console.timeEnd('search');
```

---

## 📝 Git Workflow

### Branch Strategy

```bash
main                    # Production-ready code
├── develop            # Integration branch
    ├── feature/       # Feature branches
    ├── bugfix/        # Bug fixes
    └── hotfix/        # Production hotfixes
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add voice synthesis endpoint
fix: Resolve WebSocket connection timeout
docs: Update API documentation
refactor: Simplify notification service
test: Add tests for search functionality
chore: Update dependencies
```

### Pull Request Process

1. Create feature branch
2. Make changes with clear commits
3. Write/update tests
4. Update documentation
5. Create PR with description
6. Wait for CI/CD checks
7. Address review comments
8. Merge when approved

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          cd vera_backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd vera_backend
          pytest

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node
        uses: actions/setup-node@v2
        with:
          node-version: 18
      - name: Install dependencies
        run: |
          cd vera_frontend
          npm install
      - name: Run tests
        run: |
          cd vera_frontend
          npm test
      - name: Build
        run: |
          cd vera_frontend
          npm run build
```

---

## 📚 Additional Resources

- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [React Best Practices](https://react.dev/learn/thinking-in-react)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [PostgreSQL Performance](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

*Last Updated: November 2024*
