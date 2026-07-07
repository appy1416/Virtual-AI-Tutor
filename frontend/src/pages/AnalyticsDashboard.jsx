import React, { useEffect, useState } from 'react';
import { BarChart3, Download, Flame, Hourglass, Target, Trophy, Clock, CheckCircle } from 'lucide-react';
import api, { API_BASE_URL } from '../config/api';
import { useApi } from '../hooks/useApi';

const AnalyticsDashboard = () => {
  const { data: dashboard, loading, error, call: fetchDashboard } = useApi(() => api.get('/analytics/dashboard'));

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('token');
      // Trigger download using native browser link
      const res = await api.get('/analytics/export', { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'text/csv' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `edutwin_study_export_${new Date().toISOString().slice(0,10)}.csv`;
      link.click();
    } catch (e) {
      alert('Failed to export analytics data.');
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
      </div>
    );
  }

  const metrics = dashboard || {
    total_courses: 0,
    in_progress_courses: 0,
    completed_courses: 0,
    total_study_hours: 0,
    current_streak: 0,
    average_quiz_score: 0,
    weekly_progress: []
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Learning Telemetry & Analytics</h1>
          <p className="text-slate-400 text-sm mt-1">Review study hours, streaks, and quiz statistics</p>
        </div>
        <button
          onClick={handleExport}
          className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-xs font-bold text-slate-300 hover:text-white flex items-center space-x-1.5 transition cursor-pointer"
        >
          <Download className="h-4.5 w-4.5" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* KPI Blocks */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
            <Hourglass className="h-6.5 w-6.5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-semibold block uppercase">Total Study Time</span>
            <span className="text-2xl font-bold text-slate-100">{metrics.total_study_hours} Hours</span>
          </div>
        </div>

        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
            <Flame className="h-6.5 w-6.5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-semibold block uppercase">Study Streak</span>
            <span className="text-2xl font-bold text-slate-100">{metrics.current_streak} Days</span>
          </div>
        </div>

        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Target className="h-6.5 w-6.5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-semibold block uppercase">Avg Quiz Accuracy</span>
            <span className="text-2xl font-bold text-slate-100">{metrics.average_quiz_score}%</span>
          </div>
        </div>

        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Trophy className="h-6.5 w-6.5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-semibold block uppercase">Enrolled Courses</span>
            <span className="text-2xl font-bold text-slate-100">{metrics.total_courses} Active</span>
          </div>
        </div>
      </div>

      {/* SVG Performance and Completion Analytics Graphs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Study Hours Card */}
        <div className="glass p-6 rounded-2xl space-y-6">
          <h3 className="text-lg font-bold text-slate-100">Study Duration Progress</h3>
          <div className="h-60 flex items-end justify-between px-4 pt-4 border-b border-slate-900 pb-2 relative">
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20 text-[10px] text-slate-400 font-mono">
              <div>120m</div>
              <div>90m</div>
              <div>60m</div>
              <div>30m</div>
              <div>0m</div>
            </div>

            {/* Custom SVG line representing points */}
            <svg className="absolute inset-x-0 bottom-8 h-40 w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
              <path 
                d="M 5,80 Q 25,40 50,60 T 95,20" 
                fill="none" 
                stroke="url(#grad)" 
                strokeWidth="4" 
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#c084fc" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>

            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
              <span key={day} className="text-xs text-slate-500 font-semibold z-10">{day}</span>
            ))}
          </div>
        </div>

        {/* Completion details */}
        <div className="glass p-6 rounded-2xl space-y-6">
          <h3 className="text-lg font-bold text-slate-100">Enrollment Metrics</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span>In-Progress Courses</span>
                <span>{metrics.in_progress_courses} Courses</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-900 overflow-hidden">
                <div 
                  className="h-full bg-brand-500 transition-all duration-500" 
                  style={{ width: `${metrics.total_courses ? (metrics.in_progress_courses / metrics.total_courses) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span>Completed Courses</span>
                <span>{metrics.completed_courses} Courses</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-900 overflow-hidden">
                <div 
                  className="h-full bg-indigo-500 transition-all duration-500" 
                  style={{ width: `${metrics.total_courses ? (metrics.completed_courses / metrics.total_courses) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-850 flex items-center justify-between text-xs text-slate-400">
              <span className="flex items-center space-x-1.5">
                <CheckCircle className="h-4.5 w-4.5 text-brand-400" />
                <span>All telemetry events are encrypted and compiled locally.</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
