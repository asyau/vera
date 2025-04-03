import pytest
from app.services.openai_service import get_completion

@pytest.mark.asyncio
async def test_get_completion():
    # Test with a simple prompt
    prompt = "Say hello!"
    response = await get_completion(prompt)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_get_completion_with_messages():
    # Test with messages
    messages = [
        {"role": "user", "content": "What is 2+2?"}
    ]
    response = await get_completion("", messages=messages)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0 