from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.voice import service as voice_service
from app.modules.voice import crud as voice_crud
from app.modules.voice.schemas import VoiceSessionRequest, VoiceSessionResponse, VoiceSessionDetailResponse
from app.utils.response import send_response

router = APIRouter(tags=["Voice"])

@router.post("/voice/sessions", status_code=status.HTTP_201_CREATED)
async def start_voice_session(
    body: VoiceSessionRequest,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    sess = await voice_service.create_session(
        db=db,
        student_id=current_user.id,
        tutor_type=body.tutor_type,
        lesson_id=body.lesson_id
    )
    return send_response(
        status_code=status.HTTP_201_CREATED,
        success=True,
        data=VoiceSessionResponse.model_validate(sess),
        message="Voice session opened successfully."
    )

@router.get("/voice/sessions")
async def list_voice_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    sessions, total = await voice_service.get_voice_sessions_for_student(db, current_user.id, skip, limit)
    items = [VoiceSessionResponse.model_validate(s) for s in sessions]
    
    data = {
        "items": items,
        "total_count": total
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.get("/voice/sessions/{sessionId}")
async def get_voice_session_details(
    sessionId: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    sess = await voice_crud.get_voice_session(db, sessionId)
    if not sess:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Voice session not found.")
        
    if current_user.role != "admin" and sess.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")
         
    return send_response(status_code=status.HTTP_200_OK, success=True, data=VoiceSessionDetailResponse.model_validate(sess))

@router.post("/voice/sessions/{sessionId}/upload")
async def upload_session_audio(
    sessionId: str,
    file: UploadFile = File(...),
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    from app.utils.validators import validate_audio_file
    validate_audio_file(file)

    sess = await voice_crud.get_voice_session(db, sessionId)
    if not sess:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Voice session not found.")
        
    if sess.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")

    updated = await voice_service.process_voice_upload(db, sessionId, file)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=VoiceSessionDetailResponse.model_validate(updated))

@router.get("/voice/sessions/{sessionId}/transcript")
async def get_voice_session_transcript(
    sessionId: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    sess = await voice_crud.get_voice_session(db, sessionId)
    if not sess:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Voice session not found.")
        
    if current_user.role != "admin" and sess.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")
         
    transcript = await voice_service.get_session_transcript(db, sessionId)
    return send_response(status_code=status.HTTP_200_OK, success=True, data={"transcription": transcript})

@router.post("/voice/sessions/{sessionId}/close")
async def end_voice_session(
    sessionId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    sess = await voice_crud.get_voice_session(db, sessionId)
    if not sess:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Voice session not found.")
        
    if sess.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")

    closed = await voice_service.close_session(db, sessionId)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=VoiceSessionDetailResponse.model_validate(closed))

@router.post("/voice/tts")
async def text_to_speech_mock(
    text: str,
    current_user: User = Depends(get_current_user)
):
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data={"audio_url": "/storage/audio/tts_mock_response.mp3"},
        message="Synthesized mock speech successfully."
    )
