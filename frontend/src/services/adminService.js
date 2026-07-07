import api from '../config/api';

export const adminService = {
  getUsers: (skip = 0, limit = 10) => 
    api.get('/admin/users', { params: { skip, limit } }),
    
  updateUserRole: (userId, role) => 
    api.put(`/admin/users/${userId}/role`, { role }),
    
  deactivateUser: (userId) => 
    api.post(`/admin/users/${userId}/deactivate`),
    
  reactivateUser: (userId) => 
    api.post(`/admin/users/${userId}/reactivate`),
    
  updateSettings: (settingsObj) => 
    api.put('/admin/settings', settingsObj),
    
  getSettings: () => 
    api.get('/admin/settings'),
    
  postAnnouncement: (title, content, targetAudience) => 
    api.post('/admin/announcements', {
      title,
      content,
      target_audience: targetAudience
    })
};
