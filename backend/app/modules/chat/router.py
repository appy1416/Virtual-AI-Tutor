from fastapi import APIRouter, Depends, status, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.chat import service as chat_service
from app.modules.chat import crud as chat_crud
from app.modules.chat.schemas import ChatSessionStartRequest, ChatMessageRequest, ChatSessionResponse, ChatHistoryResponse, ChatMessageResponse
from app.modules.chat.websocket_handler import manager
from app.utils.response import send_response

router = APIRouter(tags=["Chat"])

@router.post("/chat/start", status_code=status.HTTP_201_CREATED)
async def start_new_session(
    body: ChatSessionStartRequest,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    sess = await chat_service.start_chat_session(
        db=db,
        student_id=current_user.id,
        lesson_id=body.lesson_id,
        course_id=body.course_id
    )
    return send_response(status_code=status.HTTP_201_CREATED, success=True, data=ChatSessionResponse.model_validate(sess))

@router.get("/chat/sessions")
async def list_user_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    sessions, total = await chat_crud.list_chat_sessions(db, current_user.id, skip, limit)
    
    items = [ChatSessionResponse.model_validate(s) for s in sessions]
    data = {
        "items": items,
        "total_count": total
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.post("/chat/{sessionId}/message")
async def send_chat_message(
    sessionId: str,
    body: ChatMessageRequest,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    sess = await chat_crud.get_chat_session(db, sessionId)
    if not sess:
         return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Session not found.")
         
    if sess.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")
         
    res = await chat_service.send_message(db, sessionId, body.message)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=res)

@router.get("/chat/{sessionId}/messages")
async def get_session_history_list(
    sessionId: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    sess = await chat_crud.get_chat_session(db, sessionId)
    if not sess:
         return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Session not found.")
         
    if current_user.role != "admin" and sess.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")
         
    messages_mapped = [
        ChatMessageResponse(
            role=msg.get("role", ""),
            content=msg.get("content", ""),
            timestamp=msg.get("timestamp", "")
        )
        for msg in (sess.messages or [])
    ]
    return send_response(status_code=status.HTTP_200_OK, success=True, data=messages_mapped)

@router.post("/chat/{sessionId}/close")
async def close_session_record(
    sessionId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    sess = await chat_crud.get_chat_session(db, sessionId)
    if not sess:
         return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Session not found.")
         
    if sess.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")
         
    closed = await chat_service.end_session(db, sessionId)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=ChatSessionResponse.model_validate(closed))

@router.get("/chat/search")
async def search_past_conversations(
    q: str = Query(""),
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    matched_sessions = await chat_service.search_chat_history(db, current_user.id, q)
    items = [ChatSessionResponse.model_validate(s) for s in matched_sessions]
    return send_response(status_code=status.HTTP_200_OK, success=True, data=items)

# WebSocket Real-Time Chat Handler
@router.websocket("/ws/chat/{sessionId}")
async def websocket_chat_endpoint(websocket: WebSocket, sessionId: str):
    await manager.connect(sessionId, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            reply = f"WebSocket Echo response to: {data}"
            await manager.send_personal_message(reply, websocket)
    except WebSocketDisconnect:
        manager.disconnect(sessionId)
