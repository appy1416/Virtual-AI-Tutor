from fastapi import UploadFile, HTTPException, status
from typing import List, Tuple, Optional

from app.core.exceptions import EduTwinBaseException
from app.modules.voice import crud as voice_crud
from app.modules.voice.file_handler import upload_to_cloud
from app.db.models.voice import VoiceSession

async def create_session(
    db,
    student_id: str,
    tutor_type: str = "ai_voice",
    lesson_id: Optional[str] = None
) -> VoiceSession:
    return await voice_crud.create_voice_session(db, student_id, tutor_type, lesson_id)

async def process_voice_upload(
    db,
    session_id: str,
    audio_file: UploadFile
) -> Optional[VoiceSession]:
    # 1. Verify session
    sess = await voice_crud.get_voice_session(db, session_id)
    if not sess:
         raise EduTwinBaseException("Voice session not found.", status_code=status.HTTP_404_NOT_FOUND)

    # 2. Upload file
    audio_url = await upload_to_cloud(audio_file, session_id)

    # 3. Mocks STT & TTS Response Generation (Phase 3 will call real APIs)
    transcription = "Mock voice transcription query: Is energy conserved in an isolated system?"
    ai_response_audio = f"/storage/audio/mock_response_{session_id}.mp3"

    updated = await voice_crud.update_voice_session(
        db=db,
        session_id=session_id,
        transcription=transcription,
        ai_response_audio=ai_response_audio,
        audio_url=audio_url
    )
    return updated

async def close_session(db, session_id: str) -> Optional[VoiceSession]:
    return await voice_crud.close_voice_session(db, session_id)

async def get_session_transcript(db, session_id: str) -> Optional[str]:
    sess = await voice_crud.get_voice_session(db, session_id)
    return sess.transcription if sess else None

async def get_voice_sessions_for_student(
    db,
    student_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[VoiceSession], int]:
    return await voice_crud.list_voice_sessions(db, student_id, skip, limit)
