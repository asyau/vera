const API_BASE_URL = 'http://localhost:8000/api';

// Types
export interface Task {
  id: string;
  name: string;
  assignedTo: string;
  assignedToName?: string;
  dueDate?: string;
  status: string;
  description: string;
  originalPrompt: string;
  timeline: {
    createdAt: string;
    sentAt?: string;
    completedAt?: string;
  };
  assigned_user?: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'employee' | 'supervisor';
  team_id?: string;
  team_name?: string;
  company_name?: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
  role: 'employee' | 'supervisor';
}

export const api = {
  async getCompletion(prompt: string) {
    const response = await fetch(`${API_BASE_URL}/ai/respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify({
        content: prompt,
        type: 'user'
      }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
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
      mode: 'cors',
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
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  // Task API functions
  async getTasks() {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch tasks');
    }
    return response.json();
  },

  async createTask(task: Omit<Task, 'id' | 'timeline'>) {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify(task),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create task');
    }
    return response.json();
  },

  async updateTask(id: string, updates: Partial<Task>) {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update task');
    }
    return response.json();
  },

  // User API functions
  async getUsers() {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch users');
    }
    return response.json();
  },

  async getUser(userId: string) {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch user');
    }
    return response.json();
  },

  async getTeams() {
    const response = await fetch(`${API_BASE_URL}/teams`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch teams');
    }
    return response.json();
  },

  async getCompanies() {
    const response = await fetch(`${API_BASE_URL}/companies`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch companies');
    }
    return response.json();
  },

  // Authentication API functions
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify(credentials),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed');
    }
    return response.json();
  },

  async signup(userData: SignupRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify(userData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Signup failed');
    }
    return response.json();
  },

  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem('authToken');
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to get current user');
    }
    return response.json();
  },
}; 