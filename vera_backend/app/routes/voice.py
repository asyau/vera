"""
Voice Interaction API Routes
Endpoints for Speech-to-Text and Text-to-Speech
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.core.exceptions import ViraException
from app.database import get_db
from app.services.voice.voice_service import VoiceService

router = APIRouter()
logger = logging.getLogger(__name__)


class TranscriptionResponse(BaseModel):
    """Response model for speech-to-text"""

    provider: str
    text: str
    language: str
    confidence: float
    model: Optional[str] = None


class TTSRequest(BaseModel):
    """Request model for text-to-speech"""

    text: str
    voice: str = "alloy"
    provider: str = "openai"
    output_format: str = "mp3"


@router.post("/stt", response_model=TranscriptionResponse)
async def speech_to_text(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("en", description="Language code (e.g., 'en', 'es', 'fr')"),
    provider: str = Form(
        "openai", description="STT provider: openai, google, or azure"
    ),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Convert speech to text

    Supported audio formats:
    - MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM

    Supported providers:
    - openai: OpenAI Whisper (best quality)
    - google: Google Cloud Speech-to-Text
    - azure: Azure Speech Services
    """
    try:
        voice_service = VoiceService(db)

        # Read audio file
        audio_content = await audio.read()

        # Create file-like object
        from io import BytesIO

        audio_file = BytesIO(audio_content)

        # Transcribe
        result = await voice_service.speech_to_text(
            audio_file=audio_file,
            filename=audio.filename or "audio.mp3",
            language=language,
            provider=provider,
        )

        return TranscriptionResponse(**result)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"STT error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Convert text to speech

    Supported providers:
    - openai: OpenAI TTS (voices: alloy, echo, fable, onyx, nova, shimmer)
    - elevenlabs: ElevenLabs (high-quality voices, requires API key)
    - google: Google Cloud Text-to-Speech
    - azure: Azure Speech Services

    Returns audio file in the specified format (default: MP3)
    """
    try:
        voice_service = VoiceService(db)

        # Generate speech
        audio_content = await voice_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            provider=request.provider,
            output_format=request.output_format,
        )

        # Determine content type
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac",
        }

        content_type = content_type_map.get(request.output_format, "audio/mpeg")

        return Response(
            content=audio_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="speech.{request.output_format}"'
            },
        )

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


@router.get("/voices")
async def get_available_voices(
    provider: str = "openai",
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
):
    """Get list of available voices for a provider"""

    voice_lists = {
        "openai": [
            {"id": "alloy", "name": "Alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "gender": "male"},
            {"id": "fable", "name": "Fable", "gender": "neutral"},
            {"id": "onyx", "name": "Onyx", "gender": "male"},
            {"id": "nova", "name": "Nova", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female"},
        ],
        "elevenlabs": [
            {
                "id": "21m00Tcm4TlvDq8ikWAM",
                "name": "Rachel",
                "gender": "female",
                "description": "Calm and professional",
            },
            {
                "id": "AZnzlk1XvdvUeBnXmlld",
                "name": "Domi",
                "gender": "female",
                "description": "Energetic and engaging",
            },
            {
                "id": "EXAVITQu4vr4xnSDxMaL",
                "name": "Bella",
                "gender": "female",
                "description": "Soft and soothing",
            },
            {
                "id": "ErXwobaYiN019PkySvjV",
                "name": "Antoni",
                "gender": "male",
                "description": "Well-rounded and professional",
            },
            {
                "id": "MF3mGyEYCl7XYWbV9V6O",
                "name": "Elli",
                "gender": "female",
                "description": "Warm and friendly",
            },
            {
                "id": "TxGEqnHWrfWFTfGW9XjX",
                "name": "Josh",
                "gender": "male",
                "description": "Deep and authoritative",
            },
        ],
        "google": [
            {"id": "en-US-Neural2-A", "name": "Neural2-A (Male)", "gender": "male"},
            {
                "id": "en-US-Neural2-C",
                "name": "Neural2-C (Female)",
                "gender": "female",
            },
            {"id": "en-US-Neural2-D", "name": "Neural2-D (Male)", "gender": "male"},
            {
                "id": "en-US-Neural2-E",
                "name": "Neural2-E (Female)",
                "gender": "female",
            },
            {"id": "en-US-Neural2-F", "name": "Neural2-F (Female)", "gender": "female"},
            {
                "id": "en-US-Neural2-G",
                "name": "Neural2-G (Female)",
                "gender": "female",
            },
        ],
        "azure": [
            {
                "id": "en-US-JennyNeural",
                "name": "Jenny",
                "gender": "female",
                "style": "friendly",
            },
            {
                "id": "en-US-GuyNeural",
                "name": "Guy",
                "gender": "male",
                "style": "professional",
            },
            {
                "id": "en-US-AriaNeural",
                "name": "Aria",
                "gender": "female",
                "style": "warm",
            },
            {
                "id": "en-US-DavisNeural",
                "name": "Davis",
                "gender": "male",
                "style": "authoritative",
            },
        ],
    }

    return {
        "provider": provider,
        "voices": voice_lists.get(provider, []),
        "count": len(voice_lists.get(provider, [])),
    }
