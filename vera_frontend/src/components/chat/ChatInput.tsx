import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, Plus, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

// Add TypeScript definitions for SpeechRecognition
declare global {
  interface Window {
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  placeholder?: string;
  showAttachButton?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  placeholder = "Message Vira...",
  showAttachButton = false
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  
  useEffect(() => {
    // Initialize speech recognition for live transcription
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setLiveTranscript(transcript);
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);
  
  const startRecording = async () => {
    try {
      // Start live transcription
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }

      // Start audio recording for Whisper
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setIsTranscribing(true);
        await sendAudioToBackend(audioBlob);
        setIsTranscribing(false);
        
        // Stop all tracks in the stream
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setLiveTranscript('');
    }
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };
  
  const sendAudioToBackend = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      
      const response = await fetch('http://localhost:8000/api/ai/transcribe', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Failed to transcribe audio');
      }
      
      const data = await response.json();
      setMessage(prev => prev + (prev ? ' ' : '') + data.text);
    } catch (error) {
      console.error('Error transcribing audio:', error);
      alert('Error transcribing audio. Please try again.');
    }
  };
  
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 bg-white p-3 rounded-lg border shadow-sm">
      <div className="flex items-end gap-2">
        {showAttachButton && (
          <Button type="button" variant="ghost" size="icon" className="h-9 w-9 shrink-0 rounded-full">
            <Plus className="h-5 w-5 text-gray-500" />
          </Button>
        )}
        
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="min-h-10 resize-none border-0 p-2 shadow-none focus-visible:ring-0"
          autoComplete="off"
        />
        
        <div className="flex shrink-0 gap-2">
          <Button 
            type="button" 
            variant="ghost" 
            size="icon" 
            className={`h-9 w-9 rounded-full ${isRecording ? 'bg-red-100 text-red-500' : ''}`}
            onClick={toggleRecording}
            disabled={isTranscribing}
          >
            {isTranscribing ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Mic className={`h-5 w-5 ${isRecording ? 'animate-pulse' : ''}`} />
            )}
          </Button>
          
          <Button 
            type="submit" 
            size="icon" 
            className={`h-9 w-9 rounded-full ${message.trim() ? 'bg-vira-primary hover:bg-vira-primary/90' : 'bg-gray-200 text-gray-500'}`}
            disabled={!message.trim()}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      <div className="flex flex-col gap-1">
        {isRecording && liveTranscript && (
          <div className="text-sm text-gray-500 italic">
            Live transcription: {liveTranscript}
          </div>
        )}
        
        {isTranscribing && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Transcribing with Whisper...</span>
          </div>
        )}
      </div>
    </form>
  );
};

export default ChatInput;
