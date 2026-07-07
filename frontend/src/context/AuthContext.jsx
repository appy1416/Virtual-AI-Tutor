import React, { createContext, useState, useEffect } from 'react';
import api, { API_BASE_URL } from '../config/api';

export const AuthContext = createContext();

const parseJwt = (token) => {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const res = await api.get('/users/me');
          setUser(res.data.data);
        } catch (e) {
          const payload = parseJwt(token);
          if (payload) {
            setUser({
              id: payload.sub,
              role: payload.role || 'student',
              email: '',
              full_name: 'Student'
            });
          } else {
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            setToken(null);
          }
        }
      }
      setLoading(false);
    };
    initAuth();
  }, [token]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token, user: userData } = res.data.data;
    localStorage.setItem('token', access_token);
    localStorage.setItem('refreshToken', refresh_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignored
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
