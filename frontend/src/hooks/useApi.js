import { useState, useCallback } from 'react';
import { useToast } from './useToast';

export const useApi = (apiFunction) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { addToast } = useToast();

  const call = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFunction(...args);
      const result = response.data?.data ?? response.data;
      setData(result);
      if (response.data?.message) {
        addToast(response.data.message, 'success');
      }
      return result;
    } catch (err) {
      let errMsg = err.response?.data?.message || err.response?.data?.detail || err.response?.data?.error?.message || 'Something went wrong';
      if (typeof errMsg === 'object') {
        if (Array.isArray(errMsg)) {
          errMsg = errMsg.map(e => `${e.loc?.join('.') || 'error'}: ${e.msg || JSON.stringify(e)}`).join(', ');
        } else {
          errMsg = JSON.stringify(errMsg);
        }
      }
      setError(errMsg);
      addToast(errMsg, 'error');
      throw new Error(errMsg);
    } finally {
      setLoading(false);
    }
  }, [apiFunction, addToast]);

  return { data, loading, error, call, setData };
};
