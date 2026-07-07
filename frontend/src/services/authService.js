import api from '../config/api';

export const authService = {
  login: (email, password) => 
    api.post('/auth/login', { email, password }),
    
  register: (email, password, fullName) => 
    api.post('/auth/register', { email, password, full_name: fullName }),
    
  logout: () => 
    api.post('/auth/logout'),
    
  refresh: (refreshToken) => 
    api.post('/auth/refresh', {}, {
      headers: { Authorization: `Bearer ${refreshToken}` }
    })
};
