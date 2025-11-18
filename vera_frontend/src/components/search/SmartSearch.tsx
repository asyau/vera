/**
 * Smart Search Component
 * Provides intelligent search across all entities with semantic, keyword, and hybrid modes
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Filter, Loader2, X, Clock, TrendingUp, FileText, User, MessageSquare, CheckSquare } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api } from '@/services/api';
import {
  SearchEntityType,
  SearchMode,
  SearchResult,
  SearchSuggestion,
  SearchFilters,
} from '@/types/search';
import { cn } from '@/lib/utils';

interface SmartSearchProps {
  onResultClick?: (result: SearchResult) => void;
  autoFocus?: boolean;
  placeholder?: string;
  className?: string;
}

export function SmartSearch({
  onResultClick,
  autoFocus = false,
  placeholder = 'Search tasks, users, messages...',
  className,
}: SmartSearchProps) {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState<SearchMode>('hybrid');
  const [selectedTypes, setSelectedTypes] = useState<SearchEntityType[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentSearches, setRecentSearches] = useState<SearchSuggestion[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [executionTime, setExecutionTime] = useState<number>(0);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Fetch recent searches on mount
  useEffect(() => {
    api.getRecentSearches(5)
      .then(setRecentSearches)
      .catch(err => console.error('Failed to fetch recent searches:', err));
  }, []);

  // Debounced search function
  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    setShowResults(true);

    try {
      const filters: SearchFilters = {
        search_type: searchMode,
        types: selectedTypes.length > 0 ? selectedTypes : undefined,
        limit: 20,
      };

      const response = await api.search(searchQuery, filters);
      setResults(response.results);
      setExecutionTime(response.execution_time);
      setSelectedIndex(0);
    } catch (error: any) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [searchMode, selectedTypes]);

  // Handle input change with debounce
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    // Clear previous timeout
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }

    // Set new timeout for debounced search
    searchDebounceRef.current = setTimeout(() => {
      performSearch(value);
    }, 300);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showResults || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % results.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + results.length) % results.length);
        break;
      case 'Enter':
        e.preventDefault();
        if (results[selectedIndex]) {
          handleResultClick(results[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowResults(false);
        searchInputRef.current?.blur();
        break;
    }
  };

  // Handle result click
  const handleResultClick = (result: SearchResult) => {
    setShowResults(false);
    setQuery('');
    if (onResultClick) {
      onResultClick(result);
    }
  };

  // Handle recent search click
  const handleRecentSearchClick = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.query);
    performSearch(suggestion.query);
  };

  // Toggle entity type filter
  const toggleEntityType = (type: SearchEntityType) => {
    setSelectedTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  // Clear search
  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setShowResults(false);
    searchInputRef.current?.focus();
  };

  // Get icon for entity type
  const getEntityIcon = (type: SearchEntityType) => {
    switch (type) {
      case 'task':
        return <CheckSquare className="h-4 w-4" />;
      case 'user':
        return <User className="h-4 w-4" />;
      case 'conversation':
        return <MessageSquare className="h-4 w-4" />;
      case 'message':
        return <FileText className="h-4 w-4" />;
    }
  };

  // Get relevance color
  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-gray-500';
  };

  return (
    <div className={cn('relative w-full', className)}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={searchInputRef}
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowResults(true)}
          autoFocus={autoFocus}
          className="pl-10 pr-10"
        />
        {query && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearSearch}
            className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Search Controls */}
      <div className="mt-2 flex items-center gap-2">
        <Select value={searchMode} onValueChange={(value: SearchMode) => setSearchMode(value)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Search mode" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="hybrid">Hybrid</SelectItem>
            <SelectItem value="semantic">Semantic</SelectItem>
            <SelectItem value="keyword">Keyword</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex gap-1">
          {(['task', 'user', 'conversation', 'message'] as SearchEntityType[]).map(type => (
            <Button
              key={type}
              variant={selectedTypes.includes(type) ? 'default' : 'outline'}
              size="sm"
              onClick={() => toggleEntityType(type)}
              className="capitalize"
            >
              {getEntityIcon(type)}
              <span className="ml-1">{type}s</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Results Dropdown */}
      {showResults && (
        <Card className="absolute z-50 mt-2 w-full max-h-[500px] overflow-auto">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">
                {isSearching ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Searching...
                  </span>
                ) : results.length > 0 ? (
                  `${results.length} result${results.length === 1 ? '' : 's'}`
                ) : query ? (
                  'No results found'
                ) : (
                  'Recent Searches'
                )}
              </CardTitle>
              {executionTime > 0 && !isSearching && (
                <span className="text-xs text-muted-foreground">
                  {executionTime.toFixed(2)}s
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent ref={resultsRef} className="p-0">
            {!query && recentSearches.length > 0 ? (
              <div className="space-y-1 p-2">
                {recentSearches.map((suggestion, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    className="w-full justify-start text-left"
                    onClick={() => handleRecentSearchClick(suggestion)}
                  >
                    <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{suggestion.query}</span>
                    <Badge variant="outline" className="ml-auto">
                      {suggestion.count}
                    </Badge>
                  </Button>
                ))}
              </div>
            ) : results.length > 0 ? (
              <div className="space-y-1 p-2">
                {results.map((result, index) => (
                  <div
                    key={result.id}
                    onClick={() => handleResultClick(result)}
                    className={cn(
                      'flex cursor-pointer items-start gap-3 rounded-md p-3 transition-colors',
                      index === selectedIndex
                        ? 'bg-accent'
                        : 'hover:bg-accent/50'
                    )}
                  >
                    <div className="mt-1">{getEntityIcon(result.type)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium truncate">{result.title}</h4>
                        <Badge variant="outline" className="capitalize shrink-0">
                          {result.type}
                        </Badge>
                        <div className="ml-auto flex items-center gap-1">
                          <div className={cn(
                            'h-2 w-2 rounded-full',
                            getRelevanceColor(result.relevance_score)
                          )} />
                          <span className="text-xs text-muted-foreground">
                            {Math.round(result.relevance_score * 100)}%
                          </span>
                        </div>
                      </div>
                      {result.snippet && (
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {result.snippet}
                        </p>
                      )}
                      {result.metadata && Object.keys(result.metadata).length > 0 && (
                        <div className="flex gap-2 mt-2">
                          {result.metadata.status && (
                            <Badge variant="secondary" className="text-xs">
                              {result.metadata.status}
                            </Badge>
                          )}
                          {result.metadata.priority && (
                            <Badge variant="secondary" className="text-xs">
                              {result.metadata.priority}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default SmartSearch;
