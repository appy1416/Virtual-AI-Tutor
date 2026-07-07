import api from '../config/api';

export const analyticsService = {
  getDashboard: () => 
    api.get('/analytics/dashboard'),
    
  exportCsv: () => 
    api.get('/analytics/export', { responseType: 'blob' }),
    
  getAdminStats: () => 
    api.get('/admin/analytics')
};
