import api from '../config/api';

export const learningTwinService = {
  getTwinProfile: () => 
    api.get('/learning-twin'),
    
  updateTwinProfile: (learningStyle, learningPace) => 
    api.put('/learning-twin', {
      learning_style: learningStyle,
      learning_pace: learningPace
    }),
    
  getInsights: () => 
    api.get('/learning-twin/insights'),
    
  getRoadmap: () => 
    api.get('/learning-twin/roadmap')
};
