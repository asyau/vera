/**
 * Enhanced API service for Vira frontend
 * Integrates with the new microservices backend architecture
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  AuthResponse,
  LoginRequest,
  SignupRequest,
  AuthUser
} from '@/types/auth';
import {
  Task,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskAnalytics
} from '@/types/task';
import {
  Conversation,
  Message,
  CreateConversationRequest,
  SendMessageRequest
} from '@/types/chat';

class APIService {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request(config);
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || error.message || 'An error occurred';
      throw new Error(message);
    }
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>({
      method: 'POST',
      url: '/simple-auth/login',
      data: credentials,
    });
  }

  async signup(userData: SignupRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>({
      method: 'POST',
      url: '/simple-auth/signup',
      data: userData,
    });
  }

  async getCurrentUser(): Promise<AuthUser> {
    return this.request<AuthUser>({
      method: 'GET',
      url: '/simple-auth/me',
    });
  }

  async getUsers(): Promise<AuthUser[]> {
    return this.request<AuthUser[]>({
      method: 'GET',
      url: '/api/users',
    });
  }

  async logout(): Promise<void> {
    return this.request<void>({
      method: 'POST',
      url: '/api/auth/logout',
    });
  }

  // AI Chat endpoints
  async getCompletion(content: string): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: '/openai/chat',
      data: {
        content,
        type: 'user'
      },
    });
  }

  // Task Management endpoints
  async getTasks(filters?: {
    status?: string;
    includeCreated?: boolean;
    includeAssigned?: boolean;
  }): Promise<Task[]> {
    return this.request<Task[]>({
      method: 'GET',
      url: '/api/tasks/',
      params: filters,
    });
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>({
      method: 'GET',
      url: `/api/tasks/${taskId}`,
    });
  }

  async createTask(taskData: TaskCreateRequest): Promise<Task> {
    return this.request<Task>({
      method: 'POST',
      url: '/api/tasks/',
      data: taskData,
    });
  }

  async updateTask(taskId: string, updates: TaskUpdateRequest): Promise<Task> {
    return this.request<Task>({
      method: 'PUT',
      url: `/api/tasks/${taskId}`,
      data: updates,
    });
  }

  async deleteTask(taskId: string): Promise<void> {
    return this.request<void>({
      method: 'DELETE',
      url: `/api/tasks/${taskId}`,
    });
  }

  async assignTask(taskId: string, assigneeId: string): Promise<Task> {
    return this.request<Task>({
      method: 'POST',
      url: `/api/tasks/${taskId}/assign`,
      data: { assignee_id: assigneeId },
    });
  }

  async completeTask(taskId: string): Promise<Task> {
    return this.request<Task>({
      method: 'POST',
      url: `/api/tasks/${taskId}/complete`,
    });
  }

  async getOverdueTasks(): Promise<Task[]> {
    return this.request<Task[]>({
      method: 'GET',
      url: '/api/tasks/overdue/list',
    });
  }

  async getUpcomingTasks(days: number = 7): Promise<Task[]> {
    return this.request<Task[]>({
      method: 'GET',
      url: '/api/tasks/upcoming/list',
      params: { days },
    });
  }

  async searchTasks(query: string): Promise<Task[]> {
    return this.request<Task[]>({
      method: 'GET',
      url: '/api/tasks/search/query',
      params: { q: query },
    });
  }

  async getTaskAnalytics(): Promise<TaskAnalytics> {
    return this.request<TaskAnalytics>({
      method: 'GET',
      url: '/api/tasks/analytics/summary',
    });
  }

  // Conversation/Messaging endpoints
  async getConversations(): Promise<Conversation[]> {
    return this.request<Conversation[]>({
      method: 'GET',
      url: '/api/conversations/',
    });
  }

  async createConversation(data: CreateConversationRequest): Promise<Conversation> {
    return this.request<Conversation>({
      method: 'POST',
      url: '/api/conversations/',
      data,
    });
  }

  async getMessages(conversationId: string, limit: number = 50, offset: number = 0): Promise<Message[]> {
    return this.request<Message[]>({
      method: 'GET',
      url: `/api/messaging/conversations/${conversationId}/messages`,
      params: { limit, offset },
    });
  }

  async sendMessage(conversationId: string, messageData: SendMessageRequest): Promise<Message> {
    return this.request<Message>({
      method: 'POST',
      url: `/api/messaging/conversations/${conversationId}/messages`,
      data: messageData,
    });
  }

  async markMessagesAsRead(conversationId: string, messageIds?: string[]): Promise<void> {
    return this.request<void>({
      method: 'POST',
      url: `/api/messaging/conversations/${conversationId}/read`,
      data: { message_ids: messageIds },
    });
  }

  async getUnreadCount(): Promise<{ unread_count: number }> {
    return this.request<{ unread_count: number }>({
      method: 'GET',
      url: '/api/messaging/unread-count',
    });
  }

  async searchMessages(query: string, conversationId?: string): Promise<Message[]> {
    return this.request<Message[]>({
      method: 'GET',
      url: '/api/messaging/search',
      params: { q: query, conversation_id: conversationId },
    });
  }

  async createTriChatConversation(title: string, participantIds: string[]): Promise<Conversation> {
    return this.request<Conversation>({
      method: 'POST',
      url: '/api/messaging/conversations/trichat',
      data: { title, participant_ids: participantIds },
    });
  }

  async getUserPermissions(userId: string): Promise<{
    can_message: boolean;
    reason: string;
    target_user: any;
  }> {
    return this.request<{
      can_message: boolean;
      reason: string;
      target_user: any;
    }>({
      method: 'GET',
      url: `/api/messaging/users/${userId}/permissions`,
    });
  }

  async updateConversation(conversationId: string, updates: {
    title?: string;
    participants?: string[];
  }): Promise<Conversation> {
    return this.request<Conversation>({
      method: 'PUT',
      url: `/api/messaging/conversations/${conversationId}`,
      data: updates,
    });
  }

  async deleteConversation(conversationId: string): Promise<void> {
    return this.request<void>({
      method: 'DELETE',
      url: `/api/messaging/conversations/${conversationId}`,
    });
  }

  // AI/Chat endpoints
  async sendAIMessage(message: string): Promise<{ content: string; type: string }> {
    return this.request<{ content: string; type: string }>({
      method: 'POST',
      url: '/api/ai/chat',
      data: { content: message, type: 'user' },
    });
  }

  // LangChain Orchestrator endpoints
  async sendLangChainMessage(
    message: string,
    context?: Record<string, any>
  ): Promise<{
    content: string;
    intent: Record<string, any>;
    agent_used: string;
    metadata: Record<string, any>;
    cost_info?: Record<string, any>;
  }> {
    return this.request<{
      content: string;
      intent: Record<string, any>;
      agent_used: string;
      metadata: Record<string, any>;
      cost_info?: Record<string, any>;
    }>({
      method: 'POST',
      url: '/api/ai/langchain',
      data: { message, context },
    });
  }

  async analyzeIntent(message: string, context?: Record<string, any>): Promise<{
    intent_analysis: Record<string, any>;
    timestamp: string;
  }> {
    return this.request<{
      intent_analysis: Record<string, any>;
      timestamp: string;
    }>({
      method: 'POST',
      url: '/api/ai/langchain/analyze-intent',
      data: { message, context },
    });
  }

  async getOrchestratorStats(): Promise<{
    status: string;
    stats: Record<string, any>;
    timestamp: string;
  }> {
    return this.request<{
      status: string;
      stats: Record<string, any>;
      timestamp: string;
    }>({
      method: 'GET',
      url: '/api/ai/langchain/stats',
    });
  }

  async getConversationHistory(limit: number = 10): Promise<{
    history: Array<{ role: string; content: string }>;
    count: number;
    timestamp: string;
  }> {
    return this.request<{
      history: Array<{ role: string; content: string }>;
      count: number;
      timestamp: string;
    }>({
      method: 'GET',
      url: `/api/ai/langchain/conversation-history?limit=${limit}`,
    });
  }

  async clearConversationHistory(): Promise<{
    message: string;
    timestamp: string;
  }> {
    return this.request<{
      message: string;
      timestamp: string;
    }>({
      method: 'POST',
      url: '/api/ai/langchain/clear-history',
    });
  }

  // LangGraph Workflow endpoints
  async processIntelligentRequest(
    message: string,
    context?: Record<string, any>,
    forceWorkflow?: string,
    maxIterations?: number
  ): Promise<{
    response_type: string;
    content?: string;
    workflow_info?: Record<string, any>;
    intent_analysis?: Record<string, any>;
    message: string;
    next_steps?: string[];
    estimated_completion?: Record<string, any>;
    metadata?: Record<string, any>;
  }> {
    return this.request<{
      response_type: string;
      content?: string;
      workflow_info?: Record<string, any>;
      intent_analysis?: Record<string, any>;
      message: string;
      next_steps?: string[];
      estimated_completion?: Record<string, any>;
      metadata?: Record<string, any>;
    }>({
      method: 'POST',
      url: '/api/workflows/intelligent',
      data: {
        message,
        context,
        force_workflow: forceWorkflow,
        max_iterations: maxIterations,
      },
    });
  }

  async createWorkflow(
    workflowType: string,
    initialData: Record<string, any>,
    maxIterations?: number
  ): Promise<Record<string, any>> {
    return this.request<Record<string, any>>({
      method: 'POST',
      url: '/api/workflows',
      data: {
        workflow_type: workflowType,
        initial_data: initialData,
        max_iterations: maxIterations,
      },
    });
  }

  async listWorkflows(): Promise<Array<{
    workflow_id: string;
    workflow_type: string;
    status: string;
    created_at: string;
    current_step?: string;
    can_continue: boolean;
    workflow_description: string;
  }>> {
    return this.request<Array<{
      workflow_id: string;
      workflow_type: string;
      status: string;
      created_at: string;
      current_step?: string;
      can_continue: boolean;
      workflow_description: string;
    }>>({
      method: 'GET',
      url: '/api/workflows',
    });
  }

  async getWorkflowStatus(
    workflowId: string,
    threadId: string,
    workflowType: string
  ): Promise<{
    workflow_id: string;
    thread_id: string;
    workflow_type: string;
    state?: Record<string, any>;
    progress: Record<string, any>;
    can_continue: boolean;
  }> {
    return this.request<{
      workflow_id: string;
      thread_id: string;
      workflow_type: string;
      state?: Record<string, any>;
      progress: Record<string, any>;
      can_continue: boolean;
    }>({
      method: 'GET',
      url: `/api/workflows/${workflowId}/status?thread_id=${threadId}&workflow_type=${workflowType}`,
    });
  }

  async continueWorkflow(
    workflowId: string,
    threadId: string,
    workflowType: string,
    userInput?: string,
    context?: Record<string, any>
  ): Promise<Record<string, any>> {
    return this.request<Record<string, any>>({
      method: 'POST',
      url: `/api/workflows/${workflowId}/continue?thread_id=${threadId}&workflow_type=${workflowType}`,
      data: {
        user_input: userInput,
        context,
      },
    });
  }

  async cancelWorkflow(
    workflowId: string,
    threadId: string,
    workflowType: string,
    reason?: string
  ): Promise<Record<string, any>> {
    return this.request<Record<string, any>>({
      method: 'DELETE',
      url: `/api/workflows/${workflowId}?thread_id=${threadId}&workflow_type=${workflowType}&reason=${reason || ''}`,
    });
  }

  async getWorkflowTypes(): Promise<Array<Record<string, any>>> {
    return this.request<Array<Record<string, any>>>({
      method: 'GET',
      url: '/api/workflows/workflow-types',
    });
  }

  async getIntegrationCapabilities(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>({
      method: 'GET',
      url: '/api/workflows/capabilities',
    });
  }

  async getWorkflowTemplates(workflowType?: string): Promise<Record<string, any>> {
    const url = workflowType
      ? `/api/workflows/workflow-templates?workflow_type=${workflowType}`
      : '/api/workflows/workflow-templates';

    return this.request<Record<string, any>>({
      method: 'GET',
      url,
    });
  }

  async getWorkflowServiceHealth(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>({
      method: 'GET',
      url: '/api/workflows/health',
    });
  }

  async transcribeAudio(audioBlob: Blob): Promise<string> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');

    return this.request<string>({
      method: 'POST',
      url: '/api/ai/transcribe',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async generateSpeech(text: string, voice: string = 'alloy'): Promise<Blob> {
    const response = await this.client.request({
      method: 'POST',
      url: '/api/ai/speech',
      data: { text, voice },
      responseType: 'blob',
    });
    return response.data;
  }

  async extractTasks(conversation: string): Promise<any[]> {
    const result = await this.request<{ tasks: any[] }>({
      method: 'POST',
      url: '/openai/extract-tasks',
      data: { conversation },
    });
    return result.tasks || [];
  }

  async createTasksFromExtraction(extractedTasks: any[]): Promise<Task[]> {
    const createdTasks: Task[] = [];

    for (const extractedTask of extractedTasks) {
      try {
        const taskData = {
          title: extractedTask.title,
          description: extractedTask.description,
          assignee_id: extractedTask.assignee_id, // Now has resolved ID
          due_date: extractedTask.due_date,
          priority: extractedTask.priority,
          tags: extractedTask.tags || []
        };

        const createdTask = await this.createTask(taskData);
        createdTasks.push(createdTask);
      } catch (error) {
        console.error(`Failed to create task: ${extractedTask.title}`, error);
      }
    }

    return createdTasks;
  }

  async getDailySummary(): Promise<{ summary: string }> {
    return this.request<{ summary: string }>({
      method: 'GET',
      url: '/api/ai/daily-summary',
    });
  }



  async updateProfile(updates: Partial<AuthUser>): Promise<AuthUser> {
    return this.request<AuthUser>({
      method: 'PUT',
      url: '/api/users/me',
      data: updates,
    });
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    return this.request<void>({
      method: 'POST',
      url: '/api/users/me/change-password',
      data: { current_password: currentPassword, new_password: newPassword },
    });
  }

  // Additional user endpoints
  async searchUsers(query: string): Promise<AuthUser[]> {
    return this.request<AuthUser[]>({
      method: 'GET',
      url: '/api/users/search/query',
      params: { q: query },
    });
  }

  async assignUserToTeam(userId: string, teamId: string): Promise<AuthUser> {
    return this.request<AuthUser>({
      method: 'PUT',
      url: `/api/users/${userId}/team`,
      data: { team_id: teamId },
    });
  }

  async createUser(userData: {
    name: string;
    email: string;
    password: string;
    role: string;
    company_id: string;
    team_id?: string;
    project_id?: string;
    preferences?: Record<string, any>;
  }): Promise<AuthUser> {
    return this.request<AuthUser>({
      method: 'POST',
      url: '/api/users/',
      data: userData,
    });
  }

  async updateUser(userId: string, updates: Partial<AuthUser>): Promise<AuthUser> {
    return this.request<AuthUser>({
      method: 'PUT',
      url: `/api/users/${userId}`,
      data: updates,
    });
  }

  async deleteUser(userId: string): Promise<void> {
    return this.request<void>({
      method: 'DELETE',
      url: `/api/users/${userId}`,
    });
  }

  // Messaging Contacts
  async getContacts(): Promise<any[]> {
    return this.request<any[]>({
      method: 'GET',
      url: '/api/messaging/contacts',
    });
  }

  // Company/Team endpoints
  async getCompanies(): Promise<any[]> {
    return this.request<any[]>({
      method: 'GET',
      url: '/api/companies/',
    });
  }

  async getTeams(): Promise<any[]> {
    return this.request<any[]>({
      method: 'GET',
      url: '/api/teams/',
    });
  }

  async getProjects(): Promise<any[]> {
    return this.request<any[]>({
      method: 'GET',
      url: '/api/projects/',
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; services: Record<string, boolean> }> {
    return this.request<{ status: string; services: Record<string, boolean> }>({
      method: 'GET',
      url: '/health',
    });
  }

  // File upload
  async uploadFile(file: File, type: 'avatar' | 'document' | 'attachment'): Promise<{ url: string; id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    return this.request<{ url: string; id: string }>({
      method: 'POST',
      url: '/api/files/upload',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // WebSocket connection (for real-time features)
  createWebSocket(path: string): WebSocket {
    const wsUrl = this.baseURL.replace('http', 'ws') + path;
    const token = localStorage.getItem('authToken');

    const ws = new WebSocket(`${wsUrl}?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return ws;
  }

  // Integration Management Methods
  async getAvailableIntegrations(): Promise<any[]> {
    return this.request<any[]>({
      method: 'GET',
      url: '/api/integrations/available',
    });
  }

  async getCompanyIntegrations(): Promise<any[]> {
    return this.request<any[]>({
      method: 'GET',
      url: '/api/integrations/',
    });
  }

  async getIntegrationStats(): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: '/api/integrations/stats',
    });
  }

  async getIntegration(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: `/api/integrations/${integrationId}`,
    });
  }

  async getIntegrationAuthUrl(data: {
    integration_type: string;
    redirect_uri: string;
    auth_method?: string;
  }): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: '/api/integrations/auth-url',
      data,
    });
  }

  async handleIntegrationCallback(data: {
    integration_type: string;
    code?: string;
    state?: string;
    email?: string;
    api_token?: string;
    server_url?: string;
    auth_method?: string;
  }): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: '/api/integrations/callback',
      data,
    });
  }

  async testIntegration(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: `/api/integrations/${integrationId}/test`,
    });
  }

  async refreshIntegrationCredentials(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: `/api/integrations/${integrationId}/refresh`,
    });
  }

  async syncIntegrationData(integrationId: string, syncType: string = 'incremental'): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: `/api/integrations/${integrationId}/sync`,
      data: { sync_type: syncType },
    });
  }

  async disconnectIntegration(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: `/api/integrations/${integrationId}/disconnect`,
    });
  }

  async updateIntegrationConfig(integrationId: string, configUpdates: any): Promise<any> {
    return this.request<any>({
      method: 'PATCH',
      url: `/api/integrations/${integrationId}/config`,
      data: { config_updates: configUpdates },
    });
  }

  async getIntegrationEvents(integrationId: string, limit: number = 50): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: `/api/integrations/${integrationId}/events`,
      params: { limit },
    });
  }

  async syncAllIntegrations(syncType: string = 'incremental'): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: '/api/integrations/sync-all',
      data: { sync_type: syncType },
    });
  }

  // Service-specific integration methods
  async getSlackChannels(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: `/api/integrations/slack/${integrationId}/channels`,
    });
  }

  async getJiraProjects(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: `/api/integrations/jira/${integrationId}/projects`,
    });
  }

  async getGoogleCalendars(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: `/api/integrations/google/${integrationId}/calendars`,
    });
  }

  async getMicrosoftTeams(integrationId: string): Promise<any> {
    return this.request<any>({
      method: 'GET',
      url: `/api/integrations/microsoft/${integrationId}/teams`,
    });
  }

  // Calendar-specific methods
  async getCalendarEvents(integrationId: string, startDate?: string, endDate?: string): Promise<any> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    return this.request<any>({
      method: 'GET',
      url: `/api/integrations/google/${integrationId}/events`,
      params,
    });
  }

  async createCalendarEvent(integrationId: string, eventData: {
    summary: string;
    description?: string;
    start_time: string;
    end_time: string;
    timezone?: string;
    attendees?: string[];
    calendar_id?: string;
  }): Promise<any> {
    return this.request<any>({
      method: 'POST',
      url: `/api/integrations/google/${integrationId}/events`,
      data: eventData,
    });
  }
}

// Export singleton instance
export const api = new APIService();
export default api;
