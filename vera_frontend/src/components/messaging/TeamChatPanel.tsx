import React, { useState, useRef, useEffect } from 'react';
import {
  Search,
  Plus,
  MoreVertical,
  Send,
  Mic,
  Paperclip,
  AtSign,
  Users,
  User,
  MessageSquare,
  Bot,
  Filter,
  ChevronDown,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { Separator } from '@/components/ui/separator';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/services/api';

// Types for the messaging system
interface Message {
  id: string;
  content: string;
  senderId: string;
  senderName: string;
  senderRole: string;
  timestamp: string;
  type: 'user' | 'ai' | 'system';
  isViraMessage?: boolean;
  attachments?: Array<{
    id: string;
    name: string;
    type: string;
    url: string;
  }>;
}

interface Conversation {
  id: string;
  type: 'direct' | 'group';
  name: string;
  participants: Contact[];
  lastMessage?: Message;
  unreadCount: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface Contact {
  id: string;
  name: string;
  email: string;
  role: 'employee' | 'supervisor';
  team_id?: string;
  team_name?: string;
  company_name?: string;
  isOnline: boolean;
  lastSeen?: string;
  canMessage: boolean; // Based on hierarchy rules
}

const TeamChatPanel: React.FC = () => {
  const { user } = useAuthStore();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showContacts, setShowContacts] = useState(true);
  const [showConversationList, setShowConversationList] = useState(true);
  const [activeTab, setActiveTab] = useState<'conversations' | 'contacts'>('conversations');
  const [viraThinking, setViraThinking] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mock data for demonstration
  useEffect(() => {
    // Mock conversations
    const mockConversations: Conversation[] = [
      {
        id: '1',
        type: 'group',
        name: 'Marketing Team',
        participants: [
          { id: '1', name: 'John Smith', email: 'john@company.com', role: 'supervisor', isOnline: true, canMessage: true },
          { id: '2', name: 'Sarah Johnson', email: 'sarah@company.com', role: 'employee', isOnline: true, canMessage: true },
          { id: '3', name: 'Mike Davis', email: 'mike@company.com', role: 'employee', isOnline: false, canMessage: true }
        ],
        lastMessage: {
          id: 'msg1',
          content: 'Great work on the Q2 campaign!',
          senderId: '1',
          senderName: 'John Smith',
          senderRole: 'supervisor',
          timestamp: '2024-01-15T10:30:00Z',
          type: 'user'
        },
        unreadCount: 2,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-15T10:30:00Z'
      },
      {
        id: '2',
        type: 'direct',
        name: 'Sarah Johnson',
        participants: [
          { id: '2', name: 'Sarah Johnson', email: 'sarah@company.com', role: 'employee', isOnline: true, canMessage: true }
        ],
        lastMessage: {
          id: 'msg2',
          content: 'Can you review the presentation?',
          senderId: '2',
          senderName: 'Sarah Johnson',
          senderRole: 'employee',
          timestamp: '2024-01-15T09:15:00Z',
          type: 'user'
        },
        unreadCount: 0,
        isActive: false,
        createdAt: '2024-01-10T00:00:00Z',
        updatedAt: '2024-01-15T09:15:00Z'
      }
    ];

    // Mock contacts with hierarchy-based permissions
    const mockContacts: Contact[] = [
      {
        id: '1',
        name: 'John Smith',
        email: 'john@company.com',
        role: 'supervisor',
        team_id: '1',
        team_name: 'Marketing',
        company_name: 'Company Inc',
        isOnline: true,
        canMessage: true // Can message supervisor
      },
      {
        id: '2',
        name: 'Sarah Johnson',
        email: 'sarah@company.com',
        role: 'employee',
        team_id: '1',
        team_name: 'Marketing',
        company_name: 'Company Inc',
        isOnline: true,
        canMessage: true // Can message peer
      },
      {
        id: '3',
        name: 'Mike Davis',
        email: 'mike@company.com',
        role: 'employee',
        team_id: '1',
        team_name: 'Marketing',
        company_name: 'Company Inc',
        isOnline: false,
        lastSeen: '2024-01-15T08:00:00Z',
        canMessage: true // Can message peer
      },
      {
        id: '4',
        name: 'CEO Johnson',
        email: 'ceo@company.com',
        role: 'supervisor',
        team_id: 'exec',
        team_name: 'Executive',
        company_name: 'Company Inc',
        isOnline: true,
        canMessage: false // Cannot message CEO directly
      }
    ];

    setConversations(mockConversations);
    setContacts(mockContacts);

    // Set first conversation as active
    if (mockConversations.length > 0) {
      setCurrentConversation(mockConversations[0]);
      loadMessages(mockConversations[0].id);
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadMessages = (conversationId: string) => {
    // Mock messages for the conversation
    const mockMessages: Message[] = [
      {
        id: '1',
        content: "Good morning team! Let's discuss the Q2 marketing strategy.",
        senderId: '1',
        senderName: 'John Smith',
        senderRole: 'supervisor',
        timestamp: '2024-01-15T09:00:00Z',
        type: 'user'
      },
      {
        id: '2',
        content: "Hi John! I've prepared the Q1 campaign metrics. We had a 24% conversion rate overall.",
        senderId: '2',
        senderName: 'Sarah Johnson',
        senderRole: 'employee',
        timestamp: '2024-01-15T09:05:00Z',
        type: 'user'
      },
      {
        id: '3',
        content: "Based on the Q1 data, I recommend we focus more on social media channels, particularly Instagram and TikTok. Video content showed 3.2x higher engagement than static images.",
        senderId: 'vira',
        senderName: 'Vira',
        senderRole: 'ai',
        timestamp: '2024-01-15T09:07:00Z',
        type: 'ai',
        isViraMessage: true
      },
      {
        id: '4',
        content: "Excellent insight, Vira! Sarah, can you work with the creative team to shift our content strategy toward more video content?",
        senderId: '1',
        senderName: 'John Smith',
        senderRole: 'supervisor',
        timestamp: '2024-01-15T09:10:00Z',
        type: 'user'
      },
      {
        id: '5',
        content: "Absolutely! I'll set up a meeting with them today and get back to you with a revised plan by Friday.",
        senderId: '2',
        senderName: 'Sarah Johnson',
        senderRole: 'employee',
        timestamp: '2024-01-15T09:12:00Z',
        type: 'user'
      }
    ];
    setMessages(mockMessages);
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !currentConversation) return;

    const now = new Date().toISOString();
    const messageId = Date.now().toString();

    const newMsg: Message = {
      id: messageId,
      content: newMessage,
      senderId: user?.id || 'current-user',
      senderName: user?.name || 'You',
      senderRole: user?.role || 'employee',
      timestamp: now,
      type: 'user'
    };

    setMessages(prev => [...prev, newMsg]);
    setNewMessage('');

    // Check if @Vira is mentioned
    if (newMessage.includes('@Vira') || newMessage.includes('@vira')) {
      setViraThinking(true);

      try {
        // Simulate Vira response
        setTimeout(() => {
          const viraResponse: Message = {
            id: Date.now().toString(),
            content: "I've analyzed your request and can help with that. Let me gather the relevant information and get back to you shortly.",
            senderId: 'vira',
            senderName: 'Vira',
            senderRole: 'ai',
            timestamp: new Date().toISOString(),
            type: 'ai',
            isViraMessage: true
          };
          setMessages(prev => [...prev, viraResponse]);
          setViraThinking(false);
        }, 2000);
      } catch (error) {
        console.error('Error getting Vira response:', error);
        setViraThinking(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Here you would typically upload the file and get a URL
      console.log('File selected:', file.name);
    }
  };

  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.team_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredConversations = conversations.filter(conversation =>
    conversation.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conversation.participants.some(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  return (
    <div className="flex h-full bg-white">
      {/* Contact List Sidebar */}
      <div className={`${showConversationList ? 'w-80' : 'w-12'} border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out relative`}>
        {/* Toggle Button - Always Visible */}
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setShowConversationList(!showConversationList)}
          className="absolute -right-3 top-4 h-6 w-6 p-0 bg-white border border-gray-200 rounded-full shadow-sm z-10 hover:bg-gray-50"
        >
          {showConversationList ? (
            <ChevronLeft className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </Button>

        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className={`text-lg font-semibold text-gray-900 transition-opacity duration-300 ${showConversationList ? 'opacity-100' : 'opacity-0'}`}>
              Messages
            </h2>
            <div className="flex items-center space-x-2">
              {showConversationList && (
                <Button size="sm" variant="outline" onClick={() => setShowContacts(!showContacts)}>
                  <Plus className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Search */}
          <div className={`relative transition-opacity duration-300 ${showConversationList ? 'opacity-100' : 'opacity-0'}`}>
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder={activeTab === 'conversations' ? "Search conversations..." : "Search contacts..."}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Tabs */}
        <div className={`flex border-b border-gray-200 transition-opacity duration-300 ${showConversationList ? 'opacity-100' : 'opacity-0'}`}>
          <button
            onClick={() => setActiveTab('conversations')}
            className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'conversations' ? 'border-vira-primary text-vira-primary' : 'border-transparent text-gray-500'
            }`}
          >
            Conversations
          </button>
          <button
            onClick={() => setActiveTab('contacts')}
            className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'contacts' ? 'border-vira-primary text-vira-primary' : 'border-transparent text-gray-500'
            }`}
          >
            Contacts
          </button>
        </div>

        {/* Content Area */}
        <ScrollArea className={`flex-1 transition-opacity duration-300 ${showConversationList ? 'opacity-100' : 'opacity-0'}`}>
          <div className="p-2">
            {activeTab === 'conversations' ? (
              // Conversations List
              filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  currentConversation?.id === conversation.id
                    ? 'bg-vira-primary/10 border border-vira-primary/20'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => {
                  setCurrentConversation(conversation);
                  loadMessages(conversation.id);
                }}
              >
                <div className="flex items-start space-x-3">
                  <div className="relative">
                    {conversation.type === 'group' ? (
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <Users className="h-5 w-5 text-white" />
                      </div>
                    ) : (
                      <Avatar className="w-10 h-10">
                        <AvatarImage src="" />
                        <AvatarFallback className="bg-gradient-to-br from-gray-400 to-gray-600 text-white">
                          {getInitials(conversation.participants[0]?.name || '')}
                        </AvatarFallback>
                      </Avatar>
                    )}
                    {conversation.unreadCount > 0 && (
                      <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
                        {conversation.unreadCount}
                      </Badge>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {conversation.name}
                      </h3>
                      {conversation.lastMessage && (
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(conversation.lastMessage.timestamp)}
                        </span>
                      )}
                    </div>
                    {conversation.lastMessage && (
                      <p className="text-sm text-gray-500 truncate mt-1">
                        {conversation.lastMessage.senderName}: {conversation.lastMessage.content}
                      </p>
                    )}
                  </div>
                                 </div>
               </div>
             ))
            ) : (
              // Contacts List
              filteredContacts.map((contact) => (
                <div
                  key={contact.id}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    !contact.canMessage ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => {
                    if (contact.canMessage) {
                      // Create or find existing conversation with this contact
                      console.log('Start conversation with:', contact.name);
                    }
                  }}
                >
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <Avatar className="w-10 h-10">
                        <AvatarImage src="" />
                        <AvatarFallback className="bg-gradient-to-br from-gray-400 to-gray-600 text-white">
                          {getInitials(contact.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${
                        contact.isOnline ? 'bg-green-500' : 'bg-gray-400'
                      }`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {contact.name}
                        </h3>
                        {!contact.canMessage && (
                          <Badge variant="outline" className="text-xs">
                            Restricted
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 truncate">
                        {contact.role} • {contact.team_name}
                      </p>
                      {!contact.isOnline && contact.lastSeen && (
                        <p className="text-xs text-gray-400">
                          Last seen {formatTimestamp(contact.lastSeen)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentConversation ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {currentConversation.type === 'group' ? (
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <Users className="h-5 w-5 text-white" />
                    </div>
                  ) : (
                    <Avatar className="w-10 h-10">
                      <AvatarImage src="" />
                      <AvatarFallback className="bg-gradient-to-br from-gray-400 to-gray-600 text-white">
                        {getInitials(currentConversation.participants[0]?.name || '')}
                      </AvatarFallback>
                    </Avatar>
                  )}

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {currentConversation.name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {currentConversation.type === 'group'
                        ? `${currentConversation.participants.length} participants`
                        : 'Direct message'
                      }
                    </p>
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>View profile</DropdownMenuItem>
                    <DropdownMenuItem>Mute notifications</DropdownMenuItem>
                    <DropdownMenuItem>Clear chat</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.senderId === user?.id ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-xs lg:max-w-md ${
                      message.senderId === user?.id ? 'order-2' : 'order-1'
                    }`}>
                      {message.senderId !== user?.id && (
                        <div className="flex items-center space-x-2 mb-1">
                          <Avatar className="w-6 h-6">
                            <AvatarImage src="" />
                            <AvatarFallback className="text-xs bg-gradient-to-br from-gray-400 to-gray-600 text-white">
                              {message.isViraMessage ? (
                                <Bot className="h-3 w-3" />
                              ) : (
                                getInitials(message.senderName)
                              )}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-xs font-medium text-gray-700">
                            {message.senderName}
                          </span>
                          {message.isViraMessage && (
                            <Badge variant="secondary" className="text-xs">
                              AI
                            </Badge>
                          )}
                        </div>
                      )}

                      <div className={`rounded-lg px-4 py-2 ${
                        message.isViraMessage
                          ? 'bg-gradient-to-r from-vira-primary/10 to-vira-primary/5 border border-vira-primary/20'
                          : message.senderId === user?.id
                          ? 'bg-vira-primary text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <p className="text-sm">{message.content}</p>
                        <p className={`text-xs mt-1 ${
                          message.isViraMessage
                            ? 'text-vira-primary'
                            : message.senderId === user?.id
                            ? 'text-white/70'
                            : 'text-gray-500'
                        }`}>
                          {formatTimestamp(message.timestamp)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}

                {viraThinking && (
                  <div className="flex justify-start">
                    <div className="max-w-xs lg:max-w-md">
                      <div className="flex items-center space-x-2 mb-1">
                        <Avatar className="w-6 h-6">
                          <AvatarFallback className="text-xs bg-gradient-to-br from-vira-primary to-vira-primary/80 text-white">
                            <Bot className="h-3 w-3" />
                          </AvatarFallback>
                        </Avatar>
                        <span className="text-xs font-medium text-gray-700">Vira</span>
                        <Badge variant="secondary" className="text-xs">AI</Badge>
                      </div>
                      <div className="bg-gradient-to-r from-vira-primary/10 to-vira-primary/5 border border-vira-primary/20 rounded-lg px-4 py-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-vira-primary rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-vira-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-vira-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Message Input */}
            <div className="p-4 border-t border-gray-200 bg-white">
              {selectedFile && (
                <div className="mb-3 p-2 bg-gray-50 rounded-lg flex items-center justify-between">
                  <span className="text-sm text-gray-600">{selectedFile.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                  >
                    ×
                  </Button>
                </div>
              )}

              <div className="flex items-end space-x-2">
                <div className="flex-1">
                  <Textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message... Use @Vira to mention the AI assistant"
                    className="min-h-[60px] max-h-32 resize-none"
                  />
                </div>

                <div className="flex space-x-1">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setNewMessage(prev => prev + ' @Vira ')}
                    title="Mention Vira AI"
                  >
                    <AtSign className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="outline"
                    size="icon"
                  >
                    <Mic className="h-4 w-4" />
                  </Button>

                  <Button
                    onClick={handleSendMessage}
                    disabled={!newMessage.trim()}
                    size="icon"
                    className="bg-vira-primary hover:bg-vira-primary/90"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="mt-2 text-xs text-gray-500">
                Press Enter to send, Shift+Enter for new line
              </div>
            </div>
          </>
        ) : (
          /* Empty State */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a conversation</h3>
              <p className="text-gray-500">Choose a conversation from the list to start messaging</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamChatPanel;
