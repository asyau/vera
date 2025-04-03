const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  async getCompletion(prompt: string) {
    const response = await fetch(`${API_BASE_URL}/ai/respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        content: prompt,
        type: 'user'
      }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async getConversation(messages: Array<{ role: string; content: string }>) {
    const response = await fetch(`${API_BASE_URL}/ai/trichat-respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        conversation_id: Date.now().toString(),
        messages: messages,
        new_message: {
          content: messages[messages.length - 1].content,
          type: 'user'
        },
        is_at_ai: true
      }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
}; 