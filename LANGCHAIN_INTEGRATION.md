# LangChain AI Orchestrator Integration

## 🎯 Overview

This document describes the comprehensive LangChain integration for Vera's AI system. The integration introduces an intelligent orchestrator agent that understands user intent and delegates tasks to specialized agents, providing a more sophisticated and contextual AI experience.

## 🏗️ Architecture

### Core Components

1. **LangChain Orchestrator** (`langchain_orchestrator.py`)
   - Main coordination agent that analyzes user intent
   - Routes requests to appropriate specialized agents
   - Maintains conversation context and memory

2. **Specialized Agents** (via `langchain_factory.py`)
   - **Task Agent**: Handles task management, creation, and analysis
   - **Conversation Agent**: Manages general chat and Q&A
   - **Analysis Agent**: Provides data analysis and insights
   - **Coordination Agent**: Facilitates team collaboration
   - **Reporting Agent**: Generates reports and summaries

3. **Intent Analysis System**
   - Automatically classifies user requests into categories
   - Determines confidence levels and complexity
   - Extracts entities and required actions

### Intent Types Supported

- `TASK_MANAGEMENT`: Creating, updating, managing tasks
- `CONVERSATION`: General chat, Q&A, casual interactions
- `INFORMATION_RETRIEVAL`: Searching for information
- `ANALYSIS`: Data analysis, pattern recognition, insights
- `WORKFLOW_AUTOMATION`: Process automation requests
- `TEAM_COORDINATION`: Meeting scheduling, team communication
- `REPORTING`: Status reports, summaries, documentation

## 🚀 Key Features

### 1. Intelligent Intent Recognition
```python
# Automatically analyzes user intent
intent_analysis = await orchestrator._analyze_user_intent(
    "Create a task to review quarterly reports by Friday",
    user_context
)
# Returns: {
#   "primary_intent": "task_management",
#   "confidence": 0.95,
#   "entities": {"dates": ["Friday"], "tasks": ["review quarterly reports"]},
#   "complexity": "medium"
# }
```

### 2. Context-Aware Routing
- Routes requests to the most appropriate specialized agent
- Maintains conversation context across interactions
- Provides fallback mechanisms for error handling

### 3. Specialized Agent Capabilities

#### Task Agent
- Create, update, and manage tasks
- Extract actionable items from conversations
- Analyze workload and productivity patterns
- Provide task-related insights and recommendations

#### Conversation Agent
- Natural, engaging conversations
- Personalized responses based on user context
- Knowledge base integration
- Company-specific context awareness

#### Analysis Agent
- Productivity metrics analysis
- Pattern identification in user behavior
- Data-driven insights generation
- Performance trend analysis

#### Coordination Agent
- Team meeting scheduling
- Notification management
- Project dependency tracking
- Collaboration facilitation

#### Reporting Agent
- Status report generation
- Data visualization creation
- Executive summary formatting
- Custom report templates

### 4. Memory Management
- Conversation buffer window memory
- Context preservation across sessions
- User preference learning
- Interaction history tracking

## 🔧 API Endpoints

### Core LangChain Endpoints

#### 1. Main Orchestrator
```http
POST /api/ai/langchain
Content-Type: application/json

{
  "message": "Create a task to review the quarterly reports by Friday",
  "context": {
    "project_id": "proj_123",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "content": "I've created a task to review the quarterly reports with a Friday deadline...",
  "intent": {
    "primary_intent": "task_management",
    "confidence": 0.95,
    "complexity": "medium"
  },
  "agent_used": "task_agent",
  "metadata": {
    "tasks_processed": 5,
    "intent_confidence": 0.95
  },
  "cost_info": {
    "total_tokens": 150,
    "total_cost": 0.002
  }
}
```

#### 2. Intent Analysis
```http
POST /api/ai/langchain/analyze-intent
Content-Type: application/json

{
  "message": "Can you analyze my productivity this week?"
}
```

#### 3. Orchestrator Statistics
```http
GET /api/ai/langchain/stats
```

#### 4. Conversation History
```http
GET /api/ai/langchain/conversation-history?limit=10
```

#### 5. Clear History
```http
POST /api/ai/langchain/clear-history
```

### Legacy Compatibility

The existing `/api/ai/chat` endpoint now routes through the LangChain orchestrator with fallback to the original service for backward compatibility.

## 🛠️ Implementation Details

### 1. Environment Setup

Required environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4  # or preferred model
DATABASE_URL=your_database_url
```

Required dependencies (added to `requirements.txt`):
```
langchain==0.1.0
langchain-openai==0.0.5
langchain-community==0.0.10
langchain-core==0.1.0
```

### 2. Database Integration

The orchestrator integrates with existing repositories:
- `TaskRepository`: For task management operations
- `UserRepository`: For user context and team information
- Standard SQL models: `User`, `Company`, `Task`, `MemoryVector`

### 3. Memory Management

```python
# Conversation memory with 10-message window
memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=10
)
```

### 4. Cost Tracking

Each interaction includes cost information:
- Token usage tracking
- API cost calculation
- Performance metrics

## 🧪 Testing

### Running the Integration Test

```bash
cd vera_backend
python test_langchain_integration.py
```

The test suite verifies:
- Orchestrator initialization
- Intent analysis functionality
- Specialized agent creation
- Full request processing
- Conversation history management

### Test Scenarios

1. **Intent Classification Tests**
   - Task management requests
   - Conversation queries
   - Analysis requests
   - Team coordination
   - Reporting needs

2. **Agent Routing Tests**
   - Correct agent selection
   - Context preservation
   - Error handling
   - Fallback mechanisms

3. **Memory Tests**
   - Context retention
   - History retrieval
   - Memory clearing

## 🎨 Frontend Integration

### Enhanced API Service

The frontend API service (`api.ts`) now includes LangChain-specific methods:

```typescript
// Enhanced AI interaction with intent analysis
const response = await api.sendLangChainMessage(
  "Create a high-priority task for the quarterly review",
  { project_id: "proj_123" }
);

// Intent analysis for UI optimization
const intent = await api.analyzeIntent(userMessage);

// Orchestrator statistics for admin dashboard
const stats = await api.getOrchestratorStats();
```

### UI Enhancements

The integration enables:
- Intent-based UI adaptations
- Agent-specific response formatting
- Cost and performance visibility
- Enhanced conversation context

## 📊 Monitoring and Analytics

### Available Metrics

1. **Usage Statistics**
   - Agent utilization rates
   - Intent classification accuracy
   - Response times
   - Cost per interaction

2. **Performance Metrics**
   - Token usage patterns
   - Error rates by agent type
   - User satisfaction indicators
   - Conversation length analysis

3. **Business Intelligence**
   - Most common intent types
   - Agent effectiveness scores
   - User engagement patterns
   - Cost optimization opportunities

## 🔮 Future Enhancements

### Planned Features

1. **Advanced Memory Systems**
   - Long-term memory with vector storage
   - User preference learning
   - Cross-session context preservation

2. **Multi-Modal Capabilities**
   - Image analysis integration
   - Voice interaction support
   - Document processing

3. **Workflow Automation**
   - Custom workflow creation
   - Trigger-based automations
   - Integration with external tools

4. **Advanced Analytics**
   - Predictive insights
   - Behavior pattern analysis
   - Performance optimization suggestions

### Integration Opportunities

- **Calendar Systems**: Enhanced meeting scheduling
- **Project Management**: Advanced project coordination
- **Communication Platforms**: Intelligent message routing
- **Business Intelligence**: Automated report generation

## 🚨 Error Handling

### Fallback Mechanisms

1. **LangChain Failure**: Falls back to original AI service
2. **Agent Unavailable**: Routes to conversation agent
3. **Intent Analysis Failure**: Uses default conversation handling
4. **Memory Issues**: Graceful degradation without context

### Error Types

- `AIServiceError`: General AI processing errors
- `ValidationError`: Input validation failures
- `IntentAnalysisError`: Intent classification issues
- `AgentRoutingError`: Agent selection problems

## 🔐 Security Considerations

1. **API Key Management**: Secure OpenAI API key handling
2. **User Context Isolation**: Proper user data separation
3. **Memory Security**: Encrypted conversation storage
4. **Cost Controls**: Usage limits and monitoring

## 📚 Usage Examples

### 1. Task Management
```
User: "I need to create a task for reviewing the Q4 financial reports by next Friday, and assign it to John from the finance team."

Response: Uses task agent to:
- Create task with proper metadata
- Resolve "John from finance team" to user ID
- Set appropriate deadline
- Apply business rules for task creation
```

### 2. Team Coordination
```
User: "Schedule a meeting with the development team to discuss the new API architecture."

Response: Uses coordination agent to:
- Identify team members
- Suggest meeting times
- Create calendar invites
- Set up meeting agenda
```

### 3. Data Analysis
```
User: "How has my productivity been this month compared to last month?"

Response: Uses analysis agent to:
- Gather productivity metrics
- Compare time periods
- Generate insights
- Provide actionable recommendations
```

## 🎯 Success Metrics

- **Intent Accuracy**: >90% correct intent classification
- **Response Relevance**: >95% contextually appropriate responses
- **User Satisfaction**: Improved engagement metrics
- **Cost Efficiency**: Optimized token usage per interaction
- **Response Time**: <2 seconds average response time

---

This LangChain integration transforms Vera from a simple AI assistant to an intelligent orchestrator capable of understanding context, routing requests appropriately, and providing specialized expertise across different domains.
