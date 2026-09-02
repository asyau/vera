"""
File Management Service for handling file uploads and third-party integrations
"""
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import FileProcessingError, ValidationError
from app.services.base import BaseService

# Document processing imports
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    from PIL import Image
except ImportError:
    Image = None


class FileService(BaseService):
    """Service for file management and third-party storage integration"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)

        # Allowed file types and sizes
        self.allowed_types = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".xlsx"],
            "audio": [".mp3", ".wav", ".ogg", ".m4a"],
            "video": [".mp4", ".webm", ".avi", ".mov"],
        }
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        file_type: str,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload and process a file"""

        # Validate file
        self._validate_file(filename, file_data, file_type)

        # Generate unique filename
        file_id = str(uuid4())
        file_ext = Path(filename).suffix.lower()
        unique_filename = f"{file_id}{file_ext}"

        # Create file path
        type_dir = self.upload_dir / file_type
        type_dir.mkdir(exist_ok=True)
        file_path = type_dir / unique_filename

        try:
            # Save file
            with open(file_path, "wb") as f:
                file_data.seek(0)
                content = file_data.read()
                f.write(content)

            # Calculate file hash for deduplication
            file_hash = hashlib.sha256(content).hexdigest()

            # Get file info
            file_size = len(content)

            # Create file record
            file_record = {
                "id": file_id,
                "original_filename": filename,
                "stored_filename": unique_filename,
                "file_path": str(file_path),
                "file_type": file_type,
                "file_size": file_size,
                "file_hash": file_hash,
                "uploader_id": user_id,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "is_active": True,
            }

            # TODO: Store in database
            # file_entity = FileEntity(**file_record)
            # self.db.add(file_entity)
            # self.db.commit()

            # Process file based on type
            processing_result = await self._process_file(file_path, file_type, metadata)
            file_record.update(processing_result)

            return {
                "id": file_id,
                "filename": filename,
                "url": f"/files/{file_type}/{unique_filename}",
                "file_type": file_type,
                "file_size": file_size,
                "metadata": file_record.get("processed_metadata", {}),
                "created_at": file_record["created_at"].isoformat(),
            }

        except Exception as e:
            # Clean up file on error
            if file_path.exists():
                file_path.unlink()

            raise FileProcessingError(f"Failed to upload file: {str(e)}")

    async def delete_file(self, file_id: str, user_id: UUID) -> bool:
        """Delete a file"""

        try:
            # TODO: Get file record from database and verify ownership
            # file_record = self.db.query(FileEntity).filter(
            #     FileEntity.id == file_id,
            #     FileEntity.uploader_id == user_id
            # ).first()

            # For now, mock the file deletion
            return True

        except Exception as e:
            raise FileProcessingError(f"Failed to delete file: {str(e)}")

    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get file information"""

        try:
            # TODO: Implement database query
            return {
                "id": file_id,
                "filename": "example.pdf",
                "file_type": "document",
                "file_size": 1024,
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise FileProcessingError(f"Failed to get file info: {str(e)}")

    async def integrate_google_drive(
        self, user_id: UUID, credentials: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Integrate with Google Drive"""

        try:
            # Google Drive API integration
            # Requires: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

            # For full implementation:
            # 1. from googleapiclient.discovery import build
            # 2. from google.oauth2.credentials import Credentials
            # 3. Build Drive service with credentials
            # 4. Call service.files().list() to get files
            # 5. Store sync state in database

            # Stub response for now
            if not credentials:
                raise ValidationError("Google Drive credentials required")

            # Would normally call Google Drive API here
            return [
                {
                    "id": "gdrive_file_1",
                    "name": "Document.pdf",
                    "type": "application/pdf",
                    "size": 2048,
                    "modified_time": datetime.utcnow().isoformat(),
                    "web_view_link": "https://drive.google.com/file/d/example",
                    "integration_status": "configured_not_implemented",
                }
            ]

        except Exception as e:
            raise FileProcessingError(f"Google Drive integration failed: {str(e)}")

    async def integrate_dropbox(
        self, user_id: UUID, access_token: str
    ) -> List[Dict[str, Any]]:
        """Integrate with Dropbox"""

        try:
            # Dropbox API integration
            # Requires: pip install dropbox

            # For full implementation:
            # 1. import dropbox
            # 2. dbx = dropbox.Dropbox(access_token)
            # 3. result = dbx.files_list_folder("")
            # 4. Process entries and store in database
            # 5. Set up webhooks for file changes

            if not access_token:
                raise ValidationError("Dropbox access token required")

            # Would normally call Dropbox API here
            return [
                {
                    "id": "dropbox_file_1",
                    "name": "Spreadsheet.xlsx",
                    "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "size": 4096,
                    "modified_time": datetime.utcnow().isoformat(),
                    "sharing_info": {"shared": False},
                    "integration_status": "configured_not_implemented",
                }
            ]

        except Exception as e:
            raise FileProcessingError(f"Dropbox integration failed: {str(e)}")

    async def extract_text_content(self, file_path: Path) -> str:
        """Extract text content from various file types"""

        file_ext = file_path.suffix.lower()

        try:
            if file_ext == ".txt":
                return file_path.read_text(encoding="utf-8")

            elif file_ext == ".pdf":
                # Extract text from PDF using PyPDF2
                if PyPDF2 is None:
                    return "PDF extraction not available (PyPDF2 not installed)"

                try:
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        text_content = []
                        for page in pdf_reader.pages:
                            text_content.append(page.extract_text())
                        return "\n".join(text_content)
                except Exception as e:
                    raise FileProcessingError(f"PDF extraction failed: {str(e)}")

            elif file_ext in [".doc", ".docx"]:
                # Extract text from Word document using python-docx
                if file_ext == ".doc":
                    return "Legacy .doc format not supported (use .docx)"

                if DocxDocument is None:
                    return "Word extraction not available (python-docx not installed)"

                try:
                    doc = DocxDocument(file_path)
                    text_content = []
                    for paragraph in doc.paragraphs:
                        text_content.append(paragraph.text)
                    return "\n".join(text_content)
                except Exception as e:
                    raise FileProcessingError(f"Word extraction failed: {str(e)}")

            elif file_ext == ".md":
                return file_path.read_text(encoding="utf-8")

            else:
                return ""

        except Exception as e:
            raise FileProcessingError(f"Failed to extract text: {str(e)}")

    async def generate_embeddings(self, text_content: str) -> List[float]:
        """Generate embeddings for text content"""

        try:
            # TODO: Integrate with AI Orchestration Service
            # This would call the embedding generation service

            # Mock embedding for now
            return [0.1] * settings.vector_dimensions

        except Exception as e:
            raise FileProcessingError(f"Failed to generate embeddings: {str(e)}")

    def _validate_file(
        self, filename: str, file_data: BinaryIO, file_type: str
    ) -> None:
        """Validate file type, size, and content"""

        # Check file type
        if file_type not in self.allowed_types:
            raise ValidationError(f"Invalid file type: {file_type}")

        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_types[file_type]:
            raise ValidationError(
                f"File extension {file_ext} not allowed for type {file_type}"
            )

        # Check file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Reset to beginning

        if file_size > self.max_file_size:
            raise ValidationError(
                f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
            )

        if file_size == 0:
            raise ValidationError("File is empty")

    async def _process_file(
        self, file_path: Path, file_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process file based on its type"""

        processing_result = {
            "processed_at": datetime.utcnow(),
            "processed_metadata": {},
        }

        try:
            if file_type == "document":
                # Extract text content
                text_content = await self.extract_text_content(file_path)

                if text_content:
                    # Generate embeddings for search
                    embeddings = await self.generate_embeddings(text_content)

                    processing_result["processed_metadata"] = {
                        "text_content": text_content[:1000],  # Store first 1000 chars
                        "full_text_length": len(text_content),
                        "has_embeddings": True,
                        "embedding_dimensions": len(embeddings),
                    }

            elif file_type == "image":
                # Image processing (thumbnails, metadata extraction)
                if Image is None:
                    processing_result["processed_metadata"] = {
                        "thumbnail_generated": False,
                        "image_metadata": {},
                        "note": "PIL not installed",
                    }
                else:
                    try:
                        with Image.open(file_path) as img:
                            # Get image metadata
                            image_metadata = {
                                "format": img.format,
                                "mode": img.mode,
                                "width": img.width,
                                "height": img.height,
                                "size_bytes": file_path.stat().st_size,
                            }

                            # Generate thumbnail
                            thumbnail_path = file_path.parent / f"thumb_{file_path.name}"
                            img.thumbnail((200, 200))
                            img.save(thumbnail_path)

                            processing_result["processed_metadata"] = {
                                "thumbnail_generated": True,
                                "thumbnail_path": str(thumbnail_path),
                                "image_metadata": image_metadata,
                            }
                    except Exception as e:
                        processing_result["processed_metadata"] = {
                            "thumbnail_generated": False,
                            "image_metadata": {},
                            "error": str(e),
                        }

            elif file_type == "audio":
                # Audio processing (metadata extraction)
                # For transcription, would integrate with:
                # - OpenAI Whisper API
                # - Google Speech-to-Text
                # - Azure Speech Services

                try:
                    import wave
                    import contextlib

                    # Try to get audio metadata for WAV files
                    if file_path.suffix.lower() == ".wav":
                        with contextlib.closing(wave.open(str(file_path), 'r')) as f:
                            frames = f.getnframes()
                            rate = f.getframerate()
                            duration = frames / float(rate)

                            processing_result["processed_metadata"] = {
                                "duration": duration,
                                "sample_rate": rate,
                                "channels": f.getnchannels(),
                                "format": "WAV",
                                "transcription_available": False,
                                "note": "Transcription requires OpenAI/Google/Azure integration",
                            }
                    else:
                        processing_result["processed_metadata"] = {
                            "duration": 0,
                            "format": file_path.suffix[1:].upper(),
                            "transcription_available": False,
                            "note": "Metadata extraction limited for non-WAV formats",
                        }
                except Exception as e:
                    processing_result["processed_metadata"] = {
                        "duration": 0,
                        "transcription_available": False,
                        "error": str(e),
                    }

            return processing_result

        except Exception as e:
            # Log error but don't fail the upload
            processing_result["processing_error"] = str(e)
            return processing_result
