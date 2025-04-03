import os
from typing import List, Optional
from openai import OpenAI
import asyncio

# Initialize the OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize client with only the api_key parameter
client = OpenAI()

async def get_completion(prompt: str, messages: Optional[List[dict]] = None, model: str = "gpt-4o", max_tokens: int = 1000) -> str:
    """
    Get a completion from OpenAI.
    
    Args:
        prompt: The prompt to send to OpenAI.
        messages: Optional list of messages for chat-based interactions.
        model: The model to use.
        max_tokens: The maximum number of tokens to generate.
        
    Returns:
        The generated text.
    """
    try:
        # If messages are provided, use chat completion
        if messages:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        
        # Otherwise, use a system message + user prompt
        else:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": "You are Vira, an AI assistant for teams. You are helpful, concise, and professional."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        raise

async def get_summary(messages: List[str], max_tokens: int = 200) -> str:
    """
    Generate a summary of a conversation.
    
    Args:
        messages: A list of message strings to summarize.
        max_tokens: Maximum length of the summary.
        
    Returns:
        A concise summary of the conversation.
    """
    try:
        # Join messages with newlines
        conversation_text = "\n".join(messages)
        
        # Create a prompt for summarization
        prompt = f"""
        Please provide a concise summary of the following conversation:
        
        {conversation_text}
        
        Summary:
        """
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional assistant that creates concise, factual summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        raise 