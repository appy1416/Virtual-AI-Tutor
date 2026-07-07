import api from '../config/api';

export const notesService = {
  createNote: (lessonId, content) => 
    api.post(`/lessons/${lessonId}/notes`, { content }),
    
  updateNote: (noteId, content, tags = []) => 
    api.put(`/notes/${noteId}`, { content, tags }),
    
  deleteNote: (noteId) => 
    api.delete(`/notes/${noteId}`),
    
  searchNotes: (query = '') => 
    api.get(`/users/me/notes/search`, { params: { q: query } }),
    
  summarizeNote: (noteId) => 
    api.post(`/notes/${noteId}/summarize`)
};
