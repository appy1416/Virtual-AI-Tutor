import api from '../config/api';

export const chatService = {
  startSession: (lessonId = null, courseId = null) => 
    api.post('/chat/start', { lesson_id: lessonId, course_id: courseId }),
    
  sendMessage: (sessionId, message) => 
    api.post(`/chat/${sessionId}/message`, { message }),
    
  closeSession: (sessionId) => 
    api.post(`/chat/${sessionId}/close`),
    
  searchHistory: (query = '') => 
    api.get('/chat/search', { params: { q: query } })
};
