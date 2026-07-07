import api from '../config/api';

export const quizService = {
  getQuiz: (quizId) => 
    api.get(`/quizzes/${quizId}`),
    
  createQuiz: (lessonId, questionText, quizType, options, difficultyLevel, maxAttempts) => 
    api.post(`/lessons/${lessonId}/quizzes`, {
      question_text: questionText,
      quiz_type: quizType,
      options,
      difficulty_level: difficultyLevel,
      max_attempts: maxAttempts
    }),
    
  submitQuiz: (quizId, userAnswer, timeSpentSeconds = 30) => 
    api.post(`/quizzes/${quizId}/submit`, {
      user_answer: userAnswer,
      time_spent_seconds: timeSpentSeconds
    })
};
