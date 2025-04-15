import React, { useState, useEffect } from 'react';
import { CheckCircle, Calendar, Clock, AlertCircle, Volume2, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface BriefingTask {
  id: string;
  name: string;
  assignedTo: string;
  dueDate?: string;
  status: 'completed' | 'delayed' | 'upcoming';
}

const DailyBriefing: React.FC<{ open: boolean; onClose: () => void }> = ({ open, onClose }) => {
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [aiExplanation, setAiExplanation] = useState('');
  const [speechSynthesis, setSpeechSynthesis] = useState<SpeechSynthesis | null>(null);
  
  const [briefingData] = useState({
    date: today,
    completedTasks: [
      {
        id: '1',
        name: 'Follow up with client leads',
        assignedTo: 'Alex Chen',
        status: 'completed' as const
      },
      {
        id: '2',
        name: 'Finalize vendor contract',
        assignedTo: 'Jamie Wilson',
        status: 'completed' as const
      }
    ],
    delayedTasks: [
      {
        id: '3',
        name: 'Review marketing campaign proposal',
        assignedTo: 'Jamie Wilson',
        dueDate: '2025-04-03',
        status: 'delayed' as const
      }
    ],
    upcomingTasks: [
      {
        id: '4',
        name: 'Schedule meeting with investors',
        assignedTo: 'Tom Yang',
        dueDate: '2025-04-04',
        status: 'upcoming' as const
      },
      {
        id: '5',
        name: 'Finalize product roadmap',
        assignedTo: 'Raj Patel',
        dueDate: '2025-04-08',
        status: 'upcoming' as const
      }
    ],
    tomorrowTasks: [
      {
        id: '6',
        name: 'Present quarterly report to leadership',
        assignedTo: 'Sarah Johnson',
        dueDate: '2025-04-04',
        status: 'upcoming' as const
      },
      {
        id: '7',
        name: 'Review new UI designs',
        assignedTo: 'Alex Chen',
        dueDate: '2025-04-04',
        status: 'upcoming' as const
      }
    ]
  });
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  useEffect(() => {
    setSpeechSynthesis(window.speechSynthesis);
  }, []);

  const getAiExplanation = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/explain-briefing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          completed_tasks: briefingData.completedTasks,
          delayed_tasks: briefingData.delayedTasks,
          upcoming_tasks: briefingData.upcomingTasks,
          tomorrow_tasks: briefingData.tomorrowTasks,
          context: {
            date: briefingData.date,
            total_completed: briefingData.completedTasks.length,
            total_delayed: briefingData.delayedTasks.length,
            total_upcoming: briefingData.upcomingTasks.length,
            total_tomorrow: briefingData.tomorrowTasks.length
          }
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get AI explanation');
      }

      const data = await response.json();
      setAiExplanation(data.explanation);
      return data.explanation;
    } catch (error) {
      console.error('Error getting AI explanation:', error);
      const fallbackExplanation = `Today, ${briefingData.completedTasks.length} tasks have been completed, including ${briefingData.completedTasks.map(t => t.name).join(', ')}. 
      There ${briefingData.delayedTasks.length === 1 ? 'is' : 'are'} ${briefingData.delayedTasks.length} delayed task${briefingData.delayedTasks.length === 1 ? '' : 's'}, such as ${briefingData.delayedTasks.map(t => t.name).join(', ')}.
      Looking ahead, you have ${briefingData.upcomingTasks.length} upcoming task${briefingData.upcomingTasks.length === 1 ? '' : 's'} and ${briefingData.tomorrowTasks.length} task${briefingData.tomorrowTasks.length === 1 ? '' : 's'} due tomorrow.`;
      setAiExplanation(fallbackExplanation);
      return fallbackExplanation;
    } finally {
      setIsLoading(false);
    }
  };

  const speakBriefing = async () => {
    if (isSpeaking) {
      speechSynthesis?.cancel();
      setIsSpeaking(false);
      return;
    }

    try {
      setIsSpeaking(true);
      
      // Get AI explanation if we don't have one
      let textToSpeak = aiExplanation;
      if (!textToSpeak) {
        textToSpeak = await getAiExplanation();
      }

      if (textToSpeak && speechSynthesis) {
        // Get available voices
        const voices = speechSynthesis.getVoices();
        // Try to find a natural-sounding voice
        const preferredVoices = [
          'Microsoft Zira Desktop', // Windows
          'Microsoft David Desktop', // Windows
          'Google US English', // Chrome
          'Samantha', // macOS
          'Alex', // macOS
          'Daniel' // macOS
        ];
        
        let selectedVoice = voices.find(voice => 
          preferredVoices.includes(voice.name)
        ) || voices.find(voice => 
          voice.lang.includes('en') && 
          !voice.name.includes('Microsoft') && 
          !voice.name.includes('Google')
        ) || voices[0];

        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.lang = 'en-US';
        utterance.voice = selectedVoice;
        // More natural speaking rate
        utterance.rate = 0.9;
        // Slightly higher pitch for more natural sound
        utterance.pitch = 1.1;
        // Add pauses between sentences
        utterance.text = textToSpeak.replace(/\./g, '. ');
        
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);
        speechSynthesis.speak(utterance);
      }
    } catch (error) {
      console.error('Error speaking briefing:', error);
      setIsSpeaking(false);
    }
  };

  const TaskItem: React.FC<{ task: BriefingTask }> = ({ task }) => {
    const getStatusIcon = () => {
      switch (task.status) {
        case 'completed':
          return <CheckCircle className="h-4 w-4 text-green-500" />;
        case 'delayed':
          return <AlertCircle className="h-4 w-4 text-amber-500" />;
        case 'upcoming':
          return <Clock className="h-4 w-4 text-blue-500" />;
        default:
          return null;
      }
    };
    
    return (
      <div className="flex items-center space-x-3 py-2">
        <div className="flex-shrink-0">
          {getStatusIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {task.name}
          </p>
          <p className="text-xs text-gray-500 truncate">
            Assigned to {task.assignedTo}
            {task.dueDate && ` · Due ${formatDate(task.dueDate)}`}
          </p>
        </div>
      </div>
    );
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md h-[90vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-vira-primary" />
              <DialogTitle>Daily Briefing</DialogTitle>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={speakBriefing}
              disabled={isLoading}
              className={isSpeaking ? 'text-vira-primary' : ''}
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Volume2 className={`h-5 w-5 ${isSpeaking ? 'animate-pulse' : ''}`} />
              )}
            </Button>
          </div>
          <DialogDescription>
            Your summary for {briefingData.date}
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="flex-1 mt-2">
          <div className="space-y-4 pr-4">
            {briefingData.completedTasks.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Completed Today ({briefingData.completedTasks.length})
                </h3>
                <div className="space-y-1 pl-1">
                  {briefingData.completedTasks.map(task => (
                    <TaskItem key={task.id} task={task} />
                  ))}
                </div>
              </div>
            )}
            
            {briefingData.delayedTasks.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Still Pending ({briefingData.delayedTasks.length})
                  </h3>
                  <div className="space-y-1 pl-1">
                    {briefingData.delayedTasks.map(task => (
                      <TaskItem key={task.id} task={task} />
                    ))}
                  </div>
                </div>
              </>
            )}
            
            {briefingData.tomorrowTasks.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Due Tomorrow ({briefingData.tomorrowTasks.length})
                  </h3>
                  <div className="space-y-1 pl-1">
                    {briefingData.tomorrowTasks.map(task => (
                      <TaskItem key={task.id} task={task} />
                    ))}
                  </div>
                </div>
              </>
            )}
            
            {briefingData.upcomingTasks.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Upcoming Tasks ({briefingData.upcomingTasks.length})
                  </h3>
                  <div className="space-y-1 pl-1">
                    {briefingData.upcomingTasks.map(task => (
                      <TaskItem key={task.id} task={task} />
                    ))}
                  </div>
                </div>
              </>
            )}
            
            <Separator />
            
            <div className="bg-vira-light p-4 rounded-md border border-vira-primary/20">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-vira-primary">
                  AI Summary
                </h3>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={speakBriefing}
                  disabled={isLoading}
                  className={isSpeaking ? 'text-vira-primary' : ''}
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Volume2 className={`h-4 w-4 ${isSpeaking ? 'animate-pulse' : ''}`} />
                  )}
                </Button>
              </div>
              <div className="prose prose-sm max-w-none">
                {aiExplanation ? (
                  <p className="text-sm text-gray-700 whitespace-pre-line">
                    {aiExplanation}
                  </p>
                ) : (
                  <div className="flex items-center justify-center py-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={getAiExplanation}
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Generating Summary...
                        </>
                      ) : (
                        'Generate Summary'
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </ScrollArea>
        
        <DialogFooter className="flex-shrink-0 mt-4">
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button onClick={onClose}>View All Tasks</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DailyBriefing;
