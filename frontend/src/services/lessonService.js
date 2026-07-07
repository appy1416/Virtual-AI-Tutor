import api from '../config/api';

export const lessonService = {
  getLesson: (lessonId) => 
    api.get(`/lessons/${lessonId}`),
    
  createLesson: (courseId, sequenceOrder, title, description, content, estimatedDurationMinutes) => 
    api.post(`/courses/${courseId}/lessons`, {
      sequence_order: sequenceOrder,
      title,
      description,
      content,
      estimated_duration_minutes: estimatedDurationMinutes
    }),
    
  completeLesson: (lessonId) => 
    api.post(`/lessons/${lessonId}/complete`)
};
