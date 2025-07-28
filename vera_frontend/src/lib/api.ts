const API_BASE_URL = 'http://localhost:8000/api';

// Types matching the new database schema
export interface Company {
  id: string;
  name: string;
  created_at: string;
  company_profile?: Record<string, any>;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  company_id: string;
  created_at: string;
  company?: Company;
}

export interface Team {
  id: string;
  name: string;
  project_id?: string;
  company_id: string;
  supervisor_id?: string;
  created_at: string;
  project?: Project;
  company?: Company;
  supervisor?: User;
  users?: User[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  company_id: string;
  team_id?: string;
  project_id?: string;
  created_at: string;
  preferences?: Record<string, any>;
  company?: Company;
  team?: Team;
  project?: Project;
  supervised_teams?: Team[];
}

export interface Task {
  id: string;
  name: string;
  description?: string;
  status: string;
  assigned_to?: string;
  due_date?: string;
  created_by: string;
  original_prompt?: string;
  project_id?: string;
  conversation_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  priority: string;
  assignee?: User;
  creator?: User;
  project?: Project;
}

export interface Conversation {
  id: string;
  type: string;
  participant_ids: string[];
  project_id?: string;
  team_id?: string;
  created_at: string;
  last_message_at: string;
  project?: Project;
  team?: Team;
  messages?: Message[];
  tasks?: Task[];
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  type: string;
  timestamp: string;
  is_read: boolean;
  sender?: User;
  conversation?: Conversation;
}

export interface Document {
  id: string;
  file_name: string;
  file_type?: string;
  file_size?: number;
  storage_path: string;
  uploaded_by: string;
  project_id?: string;
  team_id?: string;
  created_at: string;
  processed: boolean;
  uploader?: User;
  project?: Project;
  team?: Team;
  chunks?: DocumentChunk[];
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_text: string;
  chunk_order: number;
  embedding: number[];
  created_at: string;
  document?: Document;
}

export interface MemoryVector {
  id: string;
  user_id?: string;
  company_id?: string;
  content: string;
  embedding: number[];
  timestamp: string;
  source_type?: string;
  source_id?: string;
  user?: User;
  company?: Company;
}

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  message: string;
  read_status: boolean;
  created_at: string;
  related_entity_type?: string;
  related_entity_id?: string;
  user?: User;
}

export interface Integration {
  id: string;
  company_id: string;
  integration_type: string;
  config: Record<string, any>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  company?: Company;
}

// List response types
export interface CompanyListResponse {
  companies: Company[];
  total: number;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

export interface TeamListResponse {
  teams: Team[];
  total: number;
}

export interface UserListResponse {
  users: User[];
  total: number;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface MessageListResponse {
  messages: Message[];
  total: number;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
}

export interface IntegrationListResponse {
  integrations: Integration[];
  total: number;
}

// Create/Update types
export interface CompanyCreate {
  name: string;
  company_profile?: Record<string, any>;
}

export interface CompanyUpdate {
  name?: string;
  company_profile?: Record<string, any>;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  company_id: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  company_id?: string;
}

export interface TeamCreate {
  name: string;
  project_id?: string;
  company_id: string;
  supervisor_id?: string;
}

export interface TeamUpdate {
  name?: string;
  project_id?: string;
  company_id?: string;
  supervisor_id?: string;
}

export interface UserCreate {
  name: string;
  email: string;
  role: string;
  company_id: string;
  team_id?: string;
  project_id?: string;
  preferences?: Record<string, any>;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  role?: string;
  company_id?: string;
  team_id?: string;
  project_id?: string;
  preferences?: Record<string, any>;
}

export interface TaskCreate {
  name: string;
  description?: string;
  status?: string;
  assigned_to?: string;
  due_date?: string;
  created_by: string;
  original_prompt?: string;
  project_id?: string;
  conversation_id?: string;
  priority?: string;
}

export interface TaskUpdate {
  name?: string;
  description?: string;
  status?: string;
  assigned_to?: string;
  due_date?: string;
  priority?: string;
  completed_at?: string;
}

export interface ConversationCreate {
  type: string;
  participant_ids: string[];
  project_id?: string;
  team_id?: string;
}

export interface ConversationUpdate {
  type?: string;
  participant_ids?: string[];
  project_id?: string;
  team_id?: string;
}

export interface MessageCreate {
  conversation_id: string;
  sender_id: string;
  content: string;
  type: string;
  is_read?: boolean;
}

export interface MessageUpdate {
  content?: string;
  is_read?: boolean;
}

// Authentication types
export interface AuthResponse {
  token: string;
  user: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
  role: string;
  company_id: string;
}

// API service
export const api = {
  // Company API
  async getCompanies(): Promise<CompanyListResponse> {
    const response = await fetch(`${API_BASE_URL}/companies`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch companies');
    }
    return response.json();
  },

  async getCompany(id: string): Promise<Company> {
    const response = await fetch(`${API_BASE_URL}/companies/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch company');
    }
    return response.json();
  },

  async createCompany(data: CompanyCreate): Promise<Company> {
    const response = await fetch(`${API_BASE_URL}/companies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create company');
    }
    return response.json();
  },

  async updateCompany(id: string, data: CompanyUpdate): Promise<Company> {
    const response = await fetch(`${API_BASE_URL}/companies/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update company');
    }
    return response.json();
  },

  async deleteCompany(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/companies/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete company');
    }
  },

  // Project API
  async getProjects(): Promise<ProjectListResponse> {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch projects');
    }
    return response.json();
  },

  async getProject(id: string): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch project');
    }
    return response.json();
  },

  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create project');
    }
    return response.json();
  },

  async updateProject(id: string, data: ProjectUpdate): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update project');
    }
    return response.json();
  },

  async deleteProject(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete project');
    }
  },

  // Team API
  async getTeams(): Promise<TeamListResponse> {
    const response = await fetch(`${API_BASE_URL}/teams`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch teams');
    }
    return response.json();
  },

  async getTeam(id: string): Promise<Team> {
    const response = await fetch(`${API_BASE_URL}/teams/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch team');
    }
    return response.json();
  },

  async createTeam(data: TeamCreate): Promise<Team> {
    const response = await fetch(`${API_BASE_URL}/teams`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create team');
    }
    return response.json();
  },

  async updateTeam(id: string, data: TeamUpdate): Promise<Team> {
    const response = await fetch(`${API_BASE_URL}/teams/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update team');
    }
    return response.json();
  },

  async deleteTeam(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/teams/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete team');
    }
  },

  // User API
  async getUsers(): Promise<UserListResponse> {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch users');
    }
    return response.json();
  },

  async getUser(id: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch user');
    }
    return response.json();
  },

  async createUser(data: UserCreate): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create user');
    }
    return response.json();
  },

  async updateUser(id: string, data: UserUpdate): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update user');
    }
    return response.json();
  },

  async deleteUser(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/users/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete user');
    }
  },

  // Task API
  async getTasks(): Promise<Task[]> {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch tasks');
    }
    return response.json();
  },

  async getTask(id: string): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch task');
    }
    return response.json();
  },

  async createTask(data: TaskCreate): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create task');
    }
    return response.json();
  },

  async updateTask(id: string, data: TaskUpdate): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update task');
    }
    return response.json();
  },

  async deleteTask(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete task');
    }
  },

  // Conversation API
  async getConversations(): Promise<ConversationListResponse> {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch conversations');
    }
    return response.json();
  },

  async getConversation(id: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch conversation');
    }
    return response.json();
  },

  async createConversation(data: ConversationCreate): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create conversation');
    }
    return response.json();
  },

  async updateConversation(id: string, data: ConversationUpdate): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update conversation');
    }
    return response.json();
  },

  async deleteConversation(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete conversation');
    }
  },

  // Messaging API functions
  async getContacts() {
    const response = await fetch(`${API_BASE_URL}/contacts`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch contacts');
    }
    return response.json();
  },

  async getMessages(conversationId: string) {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch messages');
    }
    return response.json();
  },

  async sendMessage(conversationId: string, content: string, attachments?: Array<{ id: string; name: string; type: string; url: string }>) {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify({
        conversation_id: conversationId,
        content,
        attachments
      }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to send message');
    }
    return response.json();
  },

  async createConversationWithParticipants(type: 'direct' | 'group', participants: string[], name?: string) {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify({
        type,
        participants,
        name
      }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create conversation');
    }
    return response.json();
  },

  async getTeamChatResponse(messages: Array<{ role: string; content: string }>) {
    const response = await fetch(`${API_BASE_URL}/ai/team-chat-respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors',
      body: JSON.stringify({
        messages: messages,
      }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to get team chat response');
    }
    return response.json();
  },

  // AI API
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

  async getAIResponse(messages: Array<{ role: string; content: string }>) {
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

  // Authentication API
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/simple-auth/login`, {
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
    const response = await fetch(`${API_BASE_URL}/simple-auth/signup`, {
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

  async getCurrentUser(): Promise<AuthResponse['user']> {
    const token = localStorage.getItem('authToken');
    const response = await fetch(`${API_BASE_URL}/simple-auth/me`, {
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