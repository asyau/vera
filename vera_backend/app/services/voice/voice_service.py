"""
Voice Interaction Service
Handles Speech-to-Text (STT) and Text-to-Speech (TTS)
"""
import logging
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ExternalServiceError, ValidationError
from app.services.base import BaseService

logger = logging.getLogger(__name__)


class VoiceService(BaseService):
    """Service for voice interaction - STT and TTS"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.upload_dir = Path("voice_uploads")
        self.upload_dir.mkdir(exist_ok=True)

    async def speech_to_text(
        self,
        audio_file: BinaryIO,
        filename: str,
        language: str = "en",
        provider: str = "openai",  # openai, google, azure
    ) -> Dict[str, Any]:
        """
        Convert speech to text using various providers

        Supported providers:
        - openai: OpenAI Whisper API
        - google: Google Cloud Speech-to-Text
        - azure: Azure Speech Services
        """

        if not settings.openai_api_key and provider == "openai":
            raise ValidationError("OpenAI API key not configured")

        try:
            if provider == "openai":
                return await self._openai_stt(audio_file, filename, language)
            elif provider == "google":
                return await self._google_stt(audio_file, filename, language)
            elif provider == "azure":
                return await self._azure_stt(audio_file, filename, language)
            else:
                raise ValidationError(f"Unsupported STT provider: {provider}")

        except Exception as e:
            raise ExternalServiceError(f"Speech-to-text failed: {str(e)}")

    async def _openai_stt(
        self, audio_file: BinaryIO, filename: str, language: str
    ) -> Dict[str, Any]:
        """OpenAI Whisper API implementation"""
        try:
            import openai

            client = openai.OpenAI(api_key=settings.openai_api_key)

            # Save audio file temporarily
            temp_path = self.upload_dir / f"{uuid4()}_{filename}"
            with open(temp_path, "wb") as f:
                f.write(audio_file.read())

            # Transcribe using Whisper
            with open(temp_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio, language=language
                )

            # Clean up temp file
            temp_path.unlink()

            return {
                "provider": "openai",
                "text": transcript.text,
                "language": language,
                "confidence": 1.0,  # Whisper doesn't provide confidence scores
                "model": "whisper-1",
            }

        except Exception as e:
            raise ExternalServiceError(f"OpenAI STT failed: {str(e)}")

    async def _google_stt(
        self, audio_file: BinaryIO, filename: str, language: str
    ) -> Dict[str, Any]:
        """Google Cloud Speech-to-Text implementation"""
        # Requires: pip install google-cloud-speech
        try:
            from google.cloud import speech

            if not settings.google_cloud_api_key:
                raise ValidationError("Google Cloud API key not configured")

            client = speech.SpeechClient()

            audio_content = audio_file.read()
            audio = speech.RecognitionAudio(content=audio_content)

            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language,
            )

            response = client.recognize(config=config, audio=audio)

            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]

                return {
                    "provider": "google",
                    "text": alternative.transcript,
                    "language": language,
                    "confidence": alternative.confidence,
                }
            else:
                return {
                    "provider": "google",
                    "text": "",
                    "language": language,
                    "confidence": 0.0,
                    "error": "No transcription results",
                }

        except ImportError:
            raise ValidationError(
                "Google Cloud Speech library not installed (pip install google-cloud-speech)"
            )
        except Exception as e:
            raise ExternalServiceError(f"Google STT failed: {str(e)}")

    async def _azure_stt(
        self, audio_file: BinaryIO, filename: str, language: str
    ) -> Dict[str, Any]:
        """Azure Speech Services implementation"""
        # Requires: pip install azure-cognitiveservices-speech
        try:
            import azure.cognitiveservices.speech as speechsdk

            # Configuration would come from settings
            speech_config = speechsdk.SpeechConfig(
                subscription=settings.azure_speech_key,  # Would need to add to settings
                region=settings.azure_speech_region,  # Would need to add to settings
            )

            speech_config.speech_recognition_language = language

            # Save audio file temporarily
            temp_path = self.upload_dir / f"{uuid4()}_{filename}"
            with open(temp_path, "wb") as f:
                f.write(audio_file.read())

            audio_config = speechsdk.audio.AudioConfig(filename=str(temp_path))
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, audio_config=audio_config
            )

            result = speech_recognizer.recognize_once()

            # Clean up temp file
            temp_path.unlink()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {
                    "provider": "azure",
                    "text": result.text,
                    "language": language,
                    "confidence": 1.0,  # Azure provides detailed confidence in JSON
                }
            else:
                return {
                    "provider": "azure",
                    "text": "",
                    "language": language,
                    "confidence": 0.0,
                    "error": str(result.reason),
                }

        except ImportError:
            raise ValidationError(
                "Azure Speech SDK not installed (pip install azure-cognitiveservices-speech)"
            )
        except AttributeError as e:
            # Settings not configured
            raise ValidationError(f"Azure Speech settings not configured: {str(e)}")
        except Exception as e:
            raise ExternalServiceError(f"Azure STT failed: {str(e)}")

    async def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        provider: str = "openai",  # openai, elevenlabs, google, azure
        output_format: str = "mp3",
    ) -> bytes:
        """
        Convert text to speech using various providers

        Supported providers:
        - openai: OpenAI TTS API
        - elevenlabs: ElevenLabs API
        - google: Google Cloud Text-to-Speech
        - azure: Azure Speech Services
        """

        if not text:
            raise ValidationError("Text cannot be empty")

        try:
            if provider == "openai":
                return await self._openai_tts(text, voice, output_format)
            elif provider == "elevenlabs":
                return await self._elevenlabs_tts(text, voice, output_format)
            elif provider == "google":
                return await self._google_tts(text, voice, output_format)
            elif provider == "azure":
                return await self._azure_tts(text, voice, output_format)
            else:
                raise ValidationError(f"Unsupported TTS provider: {provider}")

        except Exception as e:
            raise ExternalServiceError(f"Text-to-speech failed: {str(e)}")

    async def _openai_tts(
        self, text: str, voice: str, output_format: str
    ) -> bytes:
        """OpenAI TTS implementation"""
        try:
            import openai

            if not settings.openai_api_key:
                raise ValidationError("OpenAI API key not configured")

            client = openai.OpenAI(api_key=settings.openai_api_key)

            # Available voices: alloy, echo, fable, onyx, nova, shimmer
            response = client.audio.speech.create(
                model="tts-1", voice=voice, input=text, response_format=output_format
            )

            return response.content

        except Exception as e:
            raise ExternalServiceError(f"OpenAI TTS failed: {str(e)}")

    async def _elevenlabs_tts(
        self, text: str, voice: str, output_format: str
    ) -> bytes:
        """ElevenLabs TTS implementation"""
        try:
            import requests

            if not settings.elevenlabs_api_key:
                raise ValidationError("ElevenLabs API key not configured")

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": settings.elevenlabs_api_key,
            }

            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            }

            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()

            return response.content

        except Exception as e:
            raise ExternalServiceError(f"ElevenLabs TTS failed: {str(e)}")

    async def _google_tts(
        self, text: str, voice: str, output_format: str
    ) -> bytes:
        """Google Cloud Text-to-Speech implementation"""
        try:
            from google.cloud import texttospeech

            client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=text)

            voice_params = texttospeech.VoiceSelectionParams(
                language_code="en-US", name=voice
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = client.synthesize_speech(
                input=synthesis_input, voice=voice_params, audio_config=audio_config
            )

            return response.audio_content

        except ImportError:
            raise ValidationError(
                "Google Cloud TTS library not installed (pip install google-cloud-texttospeech)"
            )
        except Exception as e:
            raise ExternalServiceError(f"Google TTS failed: {str(e)}")

    async def _azure_tts(
        self, text: str, voice: str, output_format: str
    ) -> bytes:
        """Azure Speech Services TTS implementation"""
        try:
            import azure.cognitiveservices.speech as speechsdk

            speech_config = speechsdk.SpeechConfig(
                subscription=settings.azure_speech_key,
                region=settings.azure_speech_region,
            )

            speech_config.speech_synthesis_voice_name = voice

            # Use in-memory stream
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=None
            )

            result = speech_synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            else:
                raise ExternalServiceError(f"Azure TTS failed: {result.reason}")

        except ImportError:
            raise ValidationError(
                "Azure Speech SDK not installed (pip install azure-cognitiveservices-speech)"
            )
        except AttributeError as e:
            raise ValidationError(f"Azure Speech settings not configured: {str(e)}")
        except Exception as e:
            raise ExternalServiceError(f"Azure TTS failed: {str(e)}")
