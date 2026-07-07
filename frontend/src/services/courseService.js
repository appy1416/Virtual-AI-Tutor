import api from '../config/api';

export const courseService = {
  getCourses: (skip = 0, limit = 10) => 
    api.get('/courses', { params: { skip, limit } }),
    
  getCourse: (courseId) => 
    api.get(`/courses/${courseId}`),
    
  createCourse: (title, description, category, level) => 
    api.post('/courses', { title, description, category, level }),
    
  enrollCourse: (courseId) => 
    api.post(`/courses/${courseId}/enroll`),
    
  unenrollCourse: (courseId) => 
    api.post(`/courses/${courseId}/unenroll`),
    
  getEnrolledCourses: () => 
    api.get('/courses/enrolled')
};
