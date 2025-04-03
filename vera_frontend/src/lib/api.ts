const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  async getCompletion(prompt: string) {
    const response = await fetch(`${API_BASE_URL}/completion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });
    return response.json();
  },

  async getConversation(messages: Array<{ role: string; content: string }>) {
    const response = await fetch(`${API_BASE_URL}/conversation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages }),
    });
    return response.json();
  }
}; 