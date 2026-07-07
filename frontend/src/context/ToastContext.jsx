import React, { createContext, useState, useCallback } from 'react';
import { X, CheckCircle, AlertTriangle, Info, AlertOctagon } from 'lucide-react';

export const ToastContext = createContext();

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      removeToast(id);
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-emerald-400" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-amber-400" />;
      case 'error':
        return <AlertOctagon className="h-5 w-5 text-red-450" />;
      case 'info':
      default:
        return <Info className="h-5 w-5 text-indigo-400" />;
    }
  };

  const getBorderColor = (type) => {
    switch (type) {
      case 'success': return 'border-emerald-500/20 bg-emerald-500/5';
      case 'warning': return 'border-amber-500/20 bg-amber-500/5';
      case 'error': return 'border-red-500/20 bg-red-500/5';
      case 'info':
      default: return 'border-indigo-500/20 bg-indigo-500/5';
    }
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      
      {/* Floating Toasts container */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col space-y-3 w-full max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`glass p-4 rounded-xl flex items-start space-x-3 shadow-2xl border transition-all duration-300 ${getBorderColor(t.type)} animate-slide-in`}
          >
            <div className="shrink-0 mt-0.5">{getIcon(t.type)}</div>
            <div className="flex-1 text-xs text-slate-200 font-medium leading-relaxed">
              {t.message}
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="p-0.5 text-slate-500 hover:text-slate-300 rounded transition cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};
