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
    current_time = datetime.utcnow()
    """Extract task information from a prompt using OpenAI."""
    system_prompt = f"""Extract task information from the following message. 
    Return a JSON object with the following fields:
    - name: A short title for the task
    - assignedTo: The person to assign the task to
    - dueDate: Today is {current_time.strftime('%Y-%m-%d %H:%M:%S')}. Use this information for due date calculating due date. The due date in YYYY-MM-DD format (if mentioned)
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
        
        # Add task creation timestamp
        task_info['created_at'] = datetime.now().isoformat()
        
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
                    assignee_name = task.get('assignee', {}).get('name', 'Unassigned') if task.get('assignee') else 'Unassigned'
                    return f"I've created a task: '{task['name']}' assigned to {assignee_name}. Due date: {task.get('due_date', 'Not specified')}, Status: {task['status']}"
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
                system_message = """You are Vira, an AI assistant providing a personalized briefing to a team member.
                Your task is to summarize the team's progress and status in a clear, concise manner.
                
                Focus on:
                1. Individual team member contributions and progress
                2. Any delays or issues that need supervisor attention
                3. Upcoming deadlines and priorities
                4. Team workload distribution and potential bottlenecks
                5. Specific achievements and areas needing support
                
                Write as if you're directly addressing the supervisor, highlighting:
                - Who completed what tasks
                - Who is behind schedule and why
                - Who has upcoming critical deadlines
                - Any team members who might need additional support
                
                Keep it professional but conversational, as if you're giving a one-on-one update."""
            
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