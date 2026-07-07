from datetime import datetime, timezone
import logging
import os
import httpx
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.modules.chat import crud as chat_crud
from app.db.models.chat import ChatHistory

logger = logging.getLogger("edutwin.chat")

async def generate_ai_response(messages: List[Dict[str, str]]) -> str:
    is_testing = os.getenv("TESTING") == "True"
    groq_key = settings.GROQ_API_KEY
    if is_testing or not groq_key or "placeholder" in groq_key:
        logger.warning("Using offline mock fallback response (testing or key not configured).")
        last_msg = messages[-1]["content"] if messages else ""
        return f"EduTwin: I received your message: '{last_msg}'."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {groq_key}"
    }
    payload = {
        "model": settings.GROQ_CHAT_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Groq API returned status code {res.status_code}: {res.text}")
                raise httpx.HTTPStatusError(f"HTTP {res.status_code}", request=res.request, response=res)
    except Exception as e:
        logger.error(f"Failed to fetch from Groq API: {e}")
        raise e

async def start_chat_session(
    db,
    student_id: str,
    lesson_id: Optional[str] = None,
    course_id: Optional[str] = None
) -> ChatHistory:
    return await chat_crud.create_chat_session(db, student_id, lesson_id, course_id)

async def send_message(
    db,
    session_id: str,
    user_message: str
) -> Optional[Dict[str, Any]]:
    # 1. Add user message
    session = await chat_crud.add_message_to_session(db, session_id, "user", user_message)
    if not session:
        return None
        
    try:
        from app.tasks.analytics_tasks import log_chat_message
        log_chat_message.delay(session.student_id, len(user_message))
    except Exception as ex:
        logger.error(f"Failed to queue chat telemetry: {ex}")

    context_msgs = [
        {"role": "system", "content": "You are EduTwin, a helpful AI tutor companion. Answer using friendly language and markdown."}
    ]
    db_history = list(session.messages or [])
    for msg in db_history[-6:]:
        role = "user" if (msg.get("role") == "user" or msg.get("sender") == "student") else "assistant"
        context_msgs.append({"role": role, "content": msg.get("content", "")})

    # 2. AI response dialogue
    try:
        ai_response = await generate_ai_response(context_msgs)
    except Exception:
        ai_response = "I am sorry, the AI tutor service is currently unavailable. Please verify the Groq API key configuration."

    # 3. Dynamic LMS Recommendations Footer
    recs_footer = ""
    
    # Study Notes search
    try:
        from app.db.models.lms_note import LMSNote
        search_words = user_message.lower().split()
        matched_notes = []
        for word in search_words:
            if len(word) > 3:
                cursor = db.db["lms_notes"].find({
                    "$or": [
                        {"title": {"$regex": word, "$options": "i"}},
                        {"subject": {"$regex": word, "$options": "i"}}
                    ]
                }).limit(2)
                notes_found = await cursor.to_list(length=2)
                if notes_found:
                    matched_notes.extend([LMSNote(**n) for n in notes_found])
                    break
        if matched_notes:
            recs_footer += "\n\n📖 **Suggested Study Notes:**"
            for note in matched_notes:
                recs_footer += f"\n- [{note.title}]({note.file_url}) ({note.subject})"
    except Exception as e:
        logger.error(f"Failed to fetch study notes recommendations: {e}")

    # Quiz review recommendations for weak topics
    try:
        cursor = db.db["quiz_answers"].find({
            "student_id": session.student_id,
            "is_correct": False
        }).sort("attempted_at", -1).limit(2)
        failed_attempts = await cursor.to_list(length=2)
        if failed_attempts:
            recs_footer += "\n\n✏️ **Recommended Quizzes to review weak topics:**"
            seen_quizzes = set()
            for att in failed_attempts:
                quiz_id = att.get("quiz_id")
                if quiz_id and quiz_id not in seen_quizzes:
                    seen_quizzes.add(quiz_id)
                    quiz_obj = await db.db["quizzes"].find_one({"id": quiz_id})
                    if quiz_obj:
                        recs_footer += f"\n- Quiz: \"{quiz_obj.get('question_text')[:50]}...\""
    except Exception as e:
        logger.error(f"Failed to fetch quiz recommendations: {e}")

    # Append recommendations if present
    if recs_footer:
        ai_response += recs_footer

    session = await chat_crud.add_message_to_session(db, session_id, "assistant", ai_response)

    messages = list(session.messages or [])
    if len(messages) >= 2:
        return {
            "user_message": messages[-2],
            "ai_response": messages[-1]
        }
    return None

async def get_session_history(db, session_id: str) -> Optional[ChatHistory]:
    return await chat_crud.get_chat_session(db, session_id)

async def end_session(db, session_id: str) -> Optional[ChatHistory]:
    return await chat_crud.close_chat_session(db, session_id)

async def search_chat_history(db, student_id: str, query: str) -> List[ChatHistory]:
    cursor = db.db["chat_sessions"].find({"student_id": student_id})
    sessions_docs = await cursor.to_list(length=1000)
    sessions = [ChatHistory(**s) for s in sessions_docs]
    
    matched = []
    for s in sessions:
        for m in (s.messages or []):
            if query.lower() in m.get("content", "").lower():
                matched.append(s)
                break
    return matched
