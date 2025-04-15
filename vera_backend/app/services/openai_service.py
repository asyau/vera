import os
from typing import List, Optional, Dict
from openai import OpenAI
import asyncio
import json
from datetime import datetime
import uuid
import httpx

# Initialize the OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize client with only the api_key parameter
client = OpenAI(api_key=api_key)

async def extract_task_info(prompt: str) -> Dict:
    """Extract task information from a prompt using OpenAI."""
    system_prompt = """Extract task information from the following message. 
    Return a JSON object with the following fields:
    - name: A short title for the task
    - assignedTo: The person to assign the task to
    - dueDate: The due date in YYYY-MM-DD format (if mentioned)
    - status: One of 'pending', 'in-progress', 'completed', 'cancelled'
    - description: A detailed description of the task
    - originalPrompt: The original user prompt
    
    Return ONLY the JSON object, nothing else.
    """
    
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Lower temperature for more consistent JSON output
        )
        
        # Extract the JSON from the response
        content = response.choices[0].message.content.strip()
        # Remove any markdown code block syntax if present
        content = content.replace('```json', '').replace('```', '').strip()
        task_info = json.loads(content)
        
        # Add timeline information
        task_info['timeline'] = {
            'createdAt': datetime.now().isoformat(),
            'sentAt': datetime.now().isoformat()
        }
        
        return task_info
    except Exception as e:
        print(f"Error extracting task info: {str(e)}")
        raise

async def get_completion(prompt: str, messages: Optional[List[dict]] = None, model: str = "gpt-4", max_tokens: int = 1000) -> str:
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
        # Check if the prompt contains task assignment keywords and is not a briefing explanation
        task_keywords = ["assign", "task", "create task", "new task", "to do"]
        if any(keyword in prompt.lower() for keyword in task_keywords) and "briefing" not in prompt.lower():
            task_info = await extract_task_info(prompt)
            
            # Create the task
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    "http://localhost:8000/api/tasks",
                    json=task_info
                )
                if response.status_code == 200:
                    task = response.json()
                    return f"I've created a task: '{task['name']}' assigned to {task['assignedTo']}. Due date: {task.get('dueDate', 'Not specified')}, Status: {task['status']}"
                else:
                    return "I tried to create the task but encountered an error. Please try again."
        
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
            system_message = "You are Vira, an AI assistant for teams. You are helpful, concise, and professional."
            if "briefing" in prompt.lower():
                system_message = """You are Vira, an AI assistant for teams. You are analyzing a daily briefing and providing a natural, conversational summary.
                Focus on:
                1. Overall progress and achievements
                2. Areas needing attention
                3. Priority tasks for today
                4. Potential challenges and suggestions
                5. Team workload distribution
                
                Make it sound natural and engaging, as if you're explaining it to a team member but it needs to be very brief and on point."""
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
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

async def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio using OpenAI's Whisper API.
    
    Args:
        audio_file_path: Path to the audio file to transcribe.
        
    Returns:
        The transcribed text.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = await asyncio.to_thread(
                client.audio.transcriptions.create,
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return response
    except Exception as e:
        print(f"Whisper API error: {str(e)}")
        raise 