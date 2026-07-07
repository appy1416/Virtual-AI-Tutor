import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { User, Mail, Lock, AlertCircle, RefreshCw, UserPlus } from 'lucide-react';
import api from '../config/api';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [apiSuccess, setApiSuccess] = useState('');

  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const password = watch('password');

  const onSubmit = async (data) => {
    setLoading(true);
    setApiError('');
    setApiSuccess('');
    try {
      await api.post('/auth/register', {
        email: data.email,
        password: data.password,
        full_name: data.full_name
      });
      setApiSuccess('Account created successfully! Redirecting to login...');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setApiError(err.response?.data?.message || err.response?.data?.detail || 'Failed to create account. Email might be in use.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 relative">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] bg-brand-500/10 rounded-full blur-[80px] pointer-events-none" />

      <div className="glass w-full max-w-md p-8 rounded-2xl space-y-6 relative z-10">
        <div className="text-center space-y-2">
          <Link to="/" className="text-2xl font-extrabold bg-gradient-to-r from-brand-400 to-indigo-400 bg-clip-text text-transparent">
            EduTwin AI
          </Link>
          <h2 className="text-xl font-bold text-slate-100">Create Account</h2>
          <p className="text-sm text-slate-400">Join our personalized tutoring companion</p>
        </div>

        {apiError && (
          <div className="flex items-center space-x-2 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{apiError}</span>
          </div>
        )}

        {apiSuccess && (
          <div className="flex items-center space-x-2 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{apiSuccess}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-400">Full Name</label>
            <div className="relative">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
              <input
                type="text"
                placeholder="John Doe"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                {...register('full_name', { 
                  required: 'Full name is required',
                  minLength: { value: 2, message: 'Name must be at least 2 characters' }
                })}
              />
            </div>
            {errors.full_name && <span className="text-xs text-red-400">{errors.full_name.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-400">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
              <input
                type="email"
                placeholder="you@example.com"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                {...register('email', { 
                  required: 'Email is required',
                  pattern: { value: /^\S+@\S+$/i, message: 'Invalid email address' }
                })}
              />
            </div>
            {errors.email && <span className="text-xs text-red-400">{errors.email.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-400">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
              <input
                type="password"
                placeholder="Minimum 8 characters"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                {...register('password', { 
                  required: 'Password is required',
                  minLength: { value: 8, message: 'Password must be at least 8 characters' }
                })}
              />
            </div>
            {errors.password && <span className="text-xs text-red-400">{errors.password.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-400">Confirm Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
              <input
                type="password"
                placeholder="Confirm password"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                {...register('confirm_password', { 
                  required: 'Please confirm password',
                  validate: value => value === password || 'Passwords do not match'
                })}
              />
            </div>
            {errors.confirm_password && <span className="text-xs text-red-400">{errors.confirm_password.message}</span>}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 active:scale-[0.98] font-bold text-white shadow-lg shadow-brand-500/20 flex items-center justify-center space-x-2 transition cursor-pointer"
          >
            {loading ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <>
                <UserPlus className="h-5 w-5" />
                <span>Create Account</span>
              </>
            )}
          </button>
        </form>

        <div className="text-center text-sm text-slate-400 pt-2">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-400 hover:text-brand-300 font-semibold transition">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
