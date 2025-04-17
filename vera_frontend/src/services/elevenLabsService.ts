import axios from 'axios';

const ELEVEN_LABS_API_KEY = import.meta.env.VITE_ELEVEN_LABS_API_KEY;
const ELEVEN_LABS_API_URL = 'https://api.elevenlabs.io/v1';

interface ElevenLabsVoice {
  voice_id: string;
  name: string;
  preview_url: string;
}

interface ElevenLabsResponse {
  audio: string;
}

export class ElevenLabsService {
  private static instance: ElevenLabsService;
  private voices: ElevenLabsVoice[] = [];
  private selectedVoiceId: string = '';

  private constructor() {
    this.initialize();
  }

  public static getInstance(): ElevenLabsService {
    if (!ElevenLabsService.instance) {
      ElevenLabsService.instance = new ElevenLabsService();
    }
    return ElevenLabsService.instance;
  }

  private async initialize() {
    try {
      const response = await axios.get(`${ELEVEN_LABS_API_URL}/voices`, {
        headers: {
          'xi-api-key': ELEVEN_LABS_API_KEY
        }
      });
      this.voices = response.data.voices;
      // Select a professional-sounding voice by default
      this.selectedVoiceId = this.voices.find(voice => 
        voice.name.toLowerCase().includes('professional') || 
        voice.name.toLowerCase().includes('assistant')
      )?.voice_id || this.voices[0]?.voice_id || '';
    } catch (error) {
      console.error('Error initializing ElevenLabs:', error);
    }
  }

  public async textToSpeech(text: string): Promise<string> {
    try {
      const response = await axios.post(
        `${ELEVEN_LABS_API_URL}/text-to-speech/${this.selectedVoiceId}`,
        {
          text,
          model_id: 'eleven_monolingual_v1',
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75,
            style: 0.5,
            use_speaker_boost: true
          }
        },
        {
          headers: {
            'xi-api-key': ELEVEN_LABS_API_KEY,
            'Content-Type': 'application/json'
          },
          responseType: 'blob'
        }
      );

      // Create a URL for the audio blob
      const audioUrl = URL.createObjectURL(new Blob([response.data], { type: 'audio/mpeg' }));
      return audioUrl;
    } catch (error) {
      console.error('Error converting text to speech:', error);
      throw error;
    }
  }

  public async getVoices(): Promise<ElevenLabsVoice[]> {
    if (this.voices.length === 0) {
      await this.initialize();
    }
    return this.voices;
  }

  public setVoice(voiceId: string) {
    this.selectedVoiceId = voiceId;
  }
} 