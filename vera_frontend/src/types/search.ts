/**
 * Search Types
 * Type definitions for Smart Search functionality
 */

export type SearchEntityType = 'task' | 'user' | 'conversation' | 'message';
export type SearchMode = 'semantic' | 'keyword' | 'hybrid';

export interface SearchResult {
  id: string;
  type: SearchEntityType;
  title: string;
  description?: string;
  relevance_score: number;
  snippet: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SearchResponse {
  query: string;
  search_type: SearchMode;
  total_results: number;
  results: SearchResult[];
  execution_time: number;
}

export interface SearchSuggestion {
  query: string;
  count: number;
  last_searched_at: string;
}

export interface SearchStats {
  total_searches: number;
  total_indexed_entities: {
    tasks: number;
    users: number;
    conversations: number;
    messages: number;
  };
  avg_search_time: number;
  most_searched_terms: Array<{
    query: string;
    count: number;
  }>;
}

export interface SearchFilters {
  types?: SearchEntityType[];
  search_type?: SearchMode;
  limit?: number;
  offset?: number;
  min_relevance?: number;
}
