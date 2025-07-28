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

async def find_user_by_name(name: str) -> Optional[str]:
    """Find an existing user by name. Returns None if user doesn't exist."""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get("http://localhost:8000/api/users")
            if response.status_code == 200:
                users_data = response.json()
                if users_data and "users" in users_data:
                    for user in users_data["users"]:
                        if user["name"].lower() == name.lower():
                            print(f"Found existing user: {user['id']} for name: {name}")
                            return user["id"]
            
            print(f"User '{name}' not found in existing team members")
            return None
    except Exception as e:
        print(f"Error finding user by name {name}: {str(e)}")
        return None

async def get_or_create_default_user() -> Optional[str]:
    """Get or create a default user for task creation."""
    try:
        async with httpx.AsyncClient() as http_client:
            # First try to get an existing user
            response = await http_client.get("http://localhost:8000/api/users")
            if response.status_code == 200:
                users_data = response.json()
                if users_data and "users" in users_data and len(users_data["users"]) > 0:
                    user_id = users_data["users"][0]["id"]
                    print(f"Found existing user: {user_id}")
                    return user_id  # Return the first user's ID
            
            # If no users exist, we need to create a company first, then a user
            # First create a default company
            company_data = {
                "name": "Default Company",
                "company_profile": {"description": "Default company for system tasks"}
            }
            
            company_response = await http_client.post("http://localhost:8000/api/companies", json=company_data)
            if company_response.status_code != 200:
                print(f"Failed to create company: {company_response.status_code}")
                # If we can't create a company, we can't create a user, so we'll use a fallback approach
                return None
            
            company = company_response.json()
            company_id = company["id"]
            
            # Now create a default user with the company ID
            default_user_data = {
                "name": "Default User",
                "email": "default@company.com",
                "role": "Employee",
                "company_id": company_id
            }
            
            user_response = await http_client.post("http://localhost:8000/api/users", json=default_user_data)
            if user_response.status_code == 200:
                user = user_response.json()
                print(f"Created default user: {user['id']}")
                return user["id"]
            else:
                print(f"Failed to create user: {user_response.status_code}")
                return None
    except Exception as e:
        print(f"Error getting or creating default user: {str(e)}")
        return None

async def extract_task_info(prompt: str) -> Dict:    
    current_time = datetime.utcnow()
    """Extract task information from a prompt using OpenAI."""
    system_prompt = f"""Extract task information from the following message. 
    Return a JSON object with the following fields:
    - name: A short title for the task
    - description: A detailed description of the task
    - status: One of 'pending', 'in-progress', 'completed', 'cancelled'
    - priority: One of 'low', 'medium', 'high'
    - due_date: Today is {current_time.strftime('%Y-%m-%d %H:%M:%S')}. Use this information for calculating due date. The due date in YYYY-MM-DD format (if mentioned)
    - assigned_to: The name of the person to assign the task to (only if a specific person is mentioned in the prompt, otherwise null)
    - original_prompt: The original user prompt
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
        
        # Debug: Print the raw content to see what we're getting
        print(f"Raw OpenAI response: {content}")
        
        task_info = json.loads(content)
        
        # Get a valid user ID for created_by
        created_by_user_id = await get_or_create_default_user()
        if not created_by_user_id:
            # If we can't get a valid user, we can't create the task
            raise Exception("No valid user found for task creation")
        
        # Handle assigned_to field
        assigned_to_user_id = None
        assigned_to_name = task_info.get("assigned_to")
        if assigned_to_name:
            assigned_to_user_id = await find_user_by_name(assigned_to_name)
            if assigned_to_user_id:
                print(f"Assigned task to user: {assigned_to_name} (ID: {assigned_to_user_id})")
            else:
                print(f"Could not find user '{assigned_to_name}' in existing team members")
        
        # Transform the response to match TaskCreate model expectations
        transformed_task_info = {
            "name": task_info.get("name", "Untitled Task"),
            "description": task_info.get("description", ""),
            "status": task_info.get("status", "pending"),
            "priority": task_info.get("priority", "medium"),
            "due_date": task_info.get("due_date"),
            "original_prompt": task_info.get("original_prompt", prompt),
            "created_by": created_by_user_id,
            "assigned_to": assigned_to_user_id,
            "project_id": None,
            "conversation_id": None
        }
        
        return transformed_task_info
    except Exception as e:
        print(f"Error extracting task info: {str(e)}")
        # Return a default task structure if parsing fails
        created_by_user_id = await get_or_create_default_user()
        if not created_by_user_id:
            raise Exception("No valid user found for task creation")
        
        # Try to extract a name from the prompt for assignment
        assigned_to_user_id = None
        # Simple name extraction - look for common patterns like "John must", "assign to John", etc.
        import re
        name_patterns = [
            r'(\w+)\s+must\s+',
            r'assign\s+to\s+(\w+)',
            r'(\w+)\s+should\s+',
            r'(\w+)\s+needs\s+to\s+'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                name = match.group(1)
                assigned_to_user_id = await find_user_by_name(name)
                if assigned_to_user_id:
                    print(f"Extracted and assigned task to user: {name} (ID: {assigned_to_user_id})")
                break
        
        return {
            "name": "Task from conversation",
            "description": prompt,
            "status": "pending",
            "priority": "medium",
            "original_prompt": prompt,
            "created_by": created_by_user_id,
            "assigned_to": assigned_to_user_id,
            "project_id": None,
            "conversation_id": None
        }

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