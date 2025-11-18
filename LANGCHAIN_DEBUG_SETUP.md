# LangChain/LangGraph Debugging Setup

This guide explains how to set up LangSmith for debugging LangChain and LangGraph workflows in the Vira platform.

## What is LangSmith?

LangSmith is a platform for debugging, testing, and monitoring LangChain applications. It provides:
- **Tracing**: Visualize the execution flow of your LangChain chains and agents
- **Debugging**: Inspect inputs, outputs, and intermediate steps
- **Monitoring**: Track performance, costs, and errors
- **Testing**: Create test suites for your LLM applications

## Setup Instructions

### 1. Create a LangSmith Account

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Sign up for a free account
3. Create a new project (e.g., "vira-development")

### 2. Get Your API Key

1. In LangSmith, go to Settings → API Keys
2. Create a new API key
3. Copy the API key

### 3. Configure Environment Variables

Update your `.env` file in `vera_backend/`:

```bash
# LangChain/LangGraph Debugging (LangSmith)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=vira-development

# Additional debugging settings
LANGCHAIN_VERBOSE=true
LANGCHAIN_DEBUG=true
```

### 4. Verify Setup

Run the backend and check for LangSmith traces:

```bash
cd vera_backend
python -m uvicorn app.main:app --reload
```

Make a request to any LangChain/LangGraph endpoint (e.g., `/api/workflows/intelligent-request`), then check your LangSmith dashboard.

## Using LangSmith

### Viewing Traces

1. Go to your LangSmith project dashboard
2. Click on "Traces" to see all LangChain executions
3. Click on any trace to see detailed execution flow

### Key Features to Use

#### 1. Chain Visualization
- See the complete execution path of your LangChain chains
- Identify bottlenecks and slow steps
- View token usage per step

#### 2. Debugging Tools
- Inspect prompts sent to LLMs
- View LLM responses
- Check intermediate outputs
- Analyze error traces

#### 3. Performance Monitoring
- Track latency per chain/agent
- Monitor token usage and costs
- Identify slow operations

#### 4. Playground
- Test prompts interactively
- Compare different prompt versions
- Fine-tune your chains

## Debugging Workflows

### LangChain Orchestrator

The `LangChainOrchestrator` service uses LangChain agents. When enabled, you'll see:
- Intent analysis steps
- Agent tool calls
- Memory retrieval operations
- Final responses

Example trace:
```
1. User Input
2. Intent Analysis (LLM call)
3. Tool Selection
4. Task Repository Query
5. Agent Response Generation
6. Final Output
```

### LangGraph Workflows

The `LangGraphWorkflowService` uses state machines. Traces show:
- State transitions
- Node executions
- Conditional routing decisions
- Workflow completion

Example trace:
```
1. Workflow Start
2. Planning Node
3. Research Node (conditional)
4. Task Creation Node
5. Review Node
6. End State
```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing | Yes |
| `LANGCHAIN_ENDPOINT` | LangSmith API endpoint | Yes |
| `LANGCHAIN_API_KEY` | Your LangSmith API key | Yes |
| `LANGCHAIN_PROJECT` | Project name in LangSmith | Yes |
| `LANGCHAIN_VERBOSE` | Enable verbose logging | No |
| `LANGCHAIN_DEBUG` | Enable debug mode | No |

## Troubleshooting

### Traces Not Appearing

1. **Check API key**: Verify your `LANGCHAIN_API_KEY` is correct
2. **Check project name**: Ensure `LANGCHAIN_PROJECT` matches your LangSmith project
3. **Check network**: Ensure your app can reach `https://api.smith.langchain.com`
4. **Check logs**: Look for LangSmith connection errors in console

### Slow Performance

If enabling tracing slows down your app:
1. Set `LANGCHAIN_TRACING_V2=false` in production
2. Use tracing only in development/staging
3. Consider using sampling in high-traffic scenarios

### Cost Concerns

LangSmith free tier includes:
- 5,000 traces per month
- 30-day trace retention

For production, consider:
- Sampling traces (not all requests)
- Using shorter retention periods
- Upgrading to paid plan if needed

## Best Practices

1. **Development Only**: Enable full tracing in development, disable in production
2. **Use Projects**: Create separate projects for dev/staging/prod
3. **Tag Traces**: Add metadata to traces for easier filtering
4. **Monitor Costs**: Track token usage via LangSmith dashboard
5. **Create Datasets**: Build test datasets from real traces for regression testing

## Additional Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangChain Debugging Guide](https://python.langchain.com/docs/langsmith/walkthrough)
- [LangGraph Debugging](https://langchain-ai.github.io/langgraph/how-tos/debugging/)

## Vira-Specific Debugging Tips

### Task Extraction Debugging

To debug task extraction from conversations:
1. Navigate to `/api/ai/parse-task` endpoint trace
2. Check the prompt construction
3. Verify context retrieval from pgvector
4. Inspect the LLM's structured output

### Workflow Debugging

To debug LangGraph workflows:
1. Navigate to `/api/workflows/intelligent-request` trace
2. View the state transitions
3. Check each node's input/output
4. Identify which paths were taken

### Integration Debugging

To debug third-party integrations:
1. Check traces for Slack/Jira/Teams message processing
2. Verify OAuth token usage
3. Monitor API call failures
4. Track integration-triggered workflows
