
import React, { createContext, useState, useContext, useEffect } from 'react';
import { Message } from '@/components/chat/ChatPanel';

export interface ChatSession {
  id: string;
  title: string;
  date: string;
  messages: Message[];
  lastUpdated: Date;
}

interface SessionContextType {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  setCurrentSession: (sessionId: string) => void;
  createNewSession: () => void;
  addMessageToCurrentSession: (message: Message) => void;
}

// Sample initial sessions
const initialSessions: ChatSession[] = [
  {
    id: '1',
    title: 'Team Planning',
    date: 'Apr 3, 2025',
    messages: [
      {
        id: '1',
        content: "Hello! I'm Vira, your AI assistant. How can I help with team planning today?",
        type: 'ai',
        name: 'Vira',
        timestamp: '9:30 AM'
      }
    ],
    lastUpdated: new Date(2025, 3, 3)
  },
  {
    id: '2',
    title: 'Project Roadmap',
    date: 'Apr 2, 2025',
    messages: [
      {
        id: '1',
        content: "Hello! I'm Vira, your AI assistant. Let's discuss your project roadmap.",
        type: 'ai',
        name: 'Vira',
        timestamp: '10:15 AM'
      }
    ],
    lastUpdated: new Date(2025, 3, 2)
  },
  {
    id: '3',
    title: 'Budget Review',
    date: 'Apr 1, 2025',
    messages: [
      {
        id: '1',
        content: "Hello! I'm Vira, your AI assistant. Ready to help with your budget review.",
        type: 'ai',
        name: 'Vira',
        timestamp: '2:00 PM'
      }
    ],
    lastUpdated: new Date(2025, 3, 1)
  }
];

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<ChatSession[]>(initialSessions);
  const [currentSessionId, setCurrentSessionId] = useState<string>(initialSessions[0].id);

  const currentSession = sessions.find(session => session.id === currentSessionId) || null;

  const setCurrentSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Conversation',
      date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      messages: [
        {
          id: '1',
          content: "Hello! I'm Vira, your AI assistant. How can I help you today?",
          type: 'ai',
          name: 'Vira',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ],
      lastUpdated: new Date()
    };

    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  const addMessageToCurrentSession = (message: Message) => {
    if (!currentSession) return;

    setSessions(prev => prev.map(session => {
      if (session.id === currentSessionId) {
        // If it's the first user message, update the title
        let newTitle = session.title;
        if (session.title === 'New Conversation' && message.type === 'user') {
          newTitle = message.content.length > 25
            ? `${message.content.substring(0, 25)}...`
            : message.content;
        }

        return {
          ...session,
          title: newTitle,
          messages: [...session.messages, message],
          lastUpdated: new Date()
        };
      }
      return session;
    }));
  };

  return (
    <SessionContext.Provider
      value={{
        sessions,
        currentSession,
        setCurrentSession,
        createNewSession,
        addMessageToCurrentSession
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
