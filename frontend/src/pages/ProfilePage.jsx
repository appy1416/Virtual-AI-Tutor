import React, { useEffect, useState } from 'react';
import { User, Brain, AlertCircle, RefreshCw, Calendar, Award, Sparkles } from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const ProfilePage = () => {
  const { data: twin, loading: loadingTwin, call: fetchTwin } = useApi(() => api.get('/learning-twin'));
  const [selectedStyle, setSelectedStyle] = useState('mixed');
  const [selectedPace, setSelectedPace] = useState('normal');
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchTwin();
  }, []);

  useEffect(() => {
    if (twin) {
      setSelectedStyle(twin.learning_style || 'mixed');
      setSelectedPace(twin.learning_pace || 'normal');
    }
  }, [twin]);

  const handleUpdateTwin = async () => {
    setSaving(true);
    setSuccessMsg('');
    try {
      await api.put('/learning-twin', {
        learning_style: selectedStyle,
        learning_pace: selectedPace
      });
      setSuccessMsg('Learning Twin profile updated successfully!');
      fetchTwin();
    } catch (e) {
      alert('Failed to update twin parameters.');
    } finally {
      setSaving(false);
    }
  };

  if (loadingTwin) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
      </div>
    );
  }

  const profile = twin || {
    learning_style: 'mixed',
    learning_pace: 'normal',
    knowledge_gaps: [],
    next_review_items: [],
    strengths: [],
    weaknesses: []
  };

  const knowledgeGaps = Array.isArray(profile.knowledge_gaps)
    ? profile.knowledge_gaps
    : JSON.parse(profile.knowledge_gaps || '[]');

  const reviewItems = Array.isArray(profile.next_review_items)
    ? profile.next_review_items
    : JSON.parse(profile.next_review_items || '[]');

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Your Learning Twin Profile</h1>
        <p className="text-slate-400 text-sm mt-1">Review strengths, weaknesses, gaps, and spaced repetition curves</p>
      </div>

      {successMsg && (
        <div className="flex items-center space-x-2 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Col: Styles & Pace Settings */}
        <div className="glass p-6 rounded-2xl border border-slate-800 space-y-6 h-fit">
          <div className="flex items-center space-x-2 border-b border-slate-900 pb-3">
            <Brain className="h-5 w-5 text-brand-400" />
            <h3 className="text-sm font-bold text-slate-200">Twin Preferences</h3>
          </div>

          <div className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400 block">Learning Style</label>
              <select
                value={selectedStyle}
                onChange={(e) => setSelectedStyle(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-brand-500 transition cursor-pointer"
              >
                <option value="visual">Visual (Videos & Diagrams)</option>
                <option value="auditory">Auditory (Voice & Audio)</option>
                <option value="kinesthetic">Kinesthetic (Quizzes & Drafts)</option>
                <option value="mixed">Mixed (General Adaptations)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400 block">Learning Pace</label>
              <select
                value={selectedPace}
                onChange={(e) => setSelectedPace(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-brand-500 transition cursor-pointer"
              >
                <option value="slow">Slow & Guided</option>
                <option value="normal">Normal Pace</option>
                <option value="fast">Fast (Accelerated Insights)</option>
              </select>
            </div>

            <button
              onClick={handleUpdateTwin}
              disabled={saving}
              className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 font-bold text-xs text-white flex items-center justify-center space-x-2 transition disabled:opacity-50 cursor-pointer"
            >
              {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <span>Update Twin Parameters</span>}
            </button>
          </div>
        </div>

        {/* Right Col: Strengths, Gaps, Review schedules (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Strengths & Weaknesses row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="glass p-5 rounded-2xl border border-slate-850 space-y-3">
              <span className="flex items-center space-x-1.5 text-xs font-bold text-brand-400">
                <Sparkles className="h-4.5 w-4.5" />
                <span>Identified Strengths</span>
              </span>
              <div className="space-y-2">
                {profile.strengths && profile.strengths.length > 0 ? (
                  profile.strengths.map((str, i) => (
                    <div key={i} className="text-xs text-slate-300 p-2.5 rounded-lg bg-slate-900 border border-slate-850">
                      {str}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 italic py-2">
                    Completing more quizzes will identify your strengths.
                  </div>
                )}
              </div>
            </div>

            <div className="glass p-5 rounded-2xl border border-slate-850 space-y-3">
              <span className="flex items-center space-x-1.5 text-xs font-bold text-red-400">
                <AlertCircle className="h-4.5 w-4.5" />
                <span>Areas to Improve</span>
              </span>
              <div className="space-y-2">
                {profile.weaknesses && profile.weaknesses.length > 0 ? (
                  profile.weaknesses.map((w, i) => (
                    <div key={i} className="text-xs text-slate-300 p-2.5 rounded-lg bg-slate-900 border border-slate-850">
                      {w}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 italic py-2">
                    No significant weaknesses detected yet!
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Spaced Repetition curve */}
          <div className="glass p-6 rounded-2xl border border-slate-800 space-y-4">
            <span className="flex items-center space-x-1.5 text-xs font-bold text-indigo-400">
              <Calendar className="h-4.5 w-4.5" />
              <span>Review Schedule (Spaced Repetition)</span>
            </span>

            <div className="space-y-3">
              {reviewItems.length > 0 ? (
                reviewItems.map((item, i) => (
                  <div key={i} className="p-4 rounded-xl bg-slate-900 border border-slate-850 flex justify-between items-center text-xs">
                    <span className="font-bold text-slate-200">{item.concept || item.topic}</span>
                    <span className="text-brand-400 font-bold">
                      Review: {new Date(item.next_review_date).toLocaleDateString()}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-slate-500 text-xs">
                  No review schedules generated. Keep reading lessons to trigger forgetting curves!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
