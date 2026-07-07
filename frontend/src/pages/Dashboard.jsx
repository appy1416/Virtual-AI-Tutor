import React, { useEffect, useState, useContext } from 'react';
import { Link } from 'react-router-dom';
import { 
  Trophy, 
  Hourglass, 
  Target, 
  BookOpen, 
  Flame, 
  ArrowRight, 
  CheckCircle,
  Play,
  Award,
  Bell,
  Download,
  Upload,
  Calendar,
  AlertCircle
} from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';
import { AuthContext } from '../context/AuthContext';

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  
  const { data: dashboard, loading: dbLoading, call: fetchDashboard } = useApi(() => api.get('/analytics/dashboard'));
  const { data: recs, call: fetchRecs } = useApi(() => api.get('/recommendations?limit=3'));
  const { data: assignments, call: fetchAssignments } = useApi(() => api.get('/assignments'));
  const { data: sharedNotes, call: fetchSharedNotes } = useApi(() => api.get('/lms-notes'));
  const { data: notifications, call: fetchNotifications } = useApi(() => api.get('/notifications'));

  // Submission Form State
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submissionText, setSubmissionText] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Notifications Panel State
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    fetchDashboard();
    fetchRecs();
    fetchAssignments();
    fetchSharedNotes();
    fetchNotifications();
  }, []);

  const metrics = dashboard || {
    total_courses: 0,
    in_progress_courses: 0,
    completed_courses: 0,
    total_study_hours: 0,
    current_streak: user?.streak_days || 0,
    average_quiz_score: 80,
    weekly_progress: []
  };

  const recommendationItems = recs?.items || [];
  const assignmentItems = assignments || [];
  const notesItems = sharedNotes || [];
  const notificationItems = notifications || [];

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setSubmitting(true);
      const res = await api.post('/assignments/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      if (res.data?.success) {
        setUploadedFile(res.data.data);
        setSuccessMsg('File uploaded successfully!');
      } else {
        setErrorMsg('File upload failed.');
      }
    } catch (err) {
      setErrorMsg('Error uploading file: ' + (err.response?.data?.message || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmissionSubmit = async (e) => {
    e.preventDefault();
    if (!selectedAssignment) return;

    try {
      setSubmitting(true);
      setErrorMsg('');
      setSuccessMsg('');

      const res = await api.post(`/assignments/${selectedAssignment.id}/submit`, {
        submission_text: submissionText,
        file_name: uploadedFile?.file_name || '',
        file_url: uploadedFile?.file_url || ''
      });

      if (res.data?.success) {
        setSuccessMsg('Assignment submitted successfully!');
        setSubmissionText('');
        setUploadedFile(null);
        setSelectedAssignment(null);
        fetchAssignments(); // refresh state
      } else {
        setErrorMsg('Failed to submit assignment.');
      }
    } catch (err) {
      setErrorMsg('Submission error: ' + (err.response?.data?.message || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarkNotificationRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`);
      fetchNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner & Notifications Alert Bar */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Dashboard</h1>
        
        {/* Notification Bell Dropdown */}
        <div className="relative">
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-3 rounded-full bg-slate-900 border border-slate-800 hover:border-brand-500/50 hover:text-white transition flex items-center justify-center cursor-pointer"
          >
            <Bell className="h-5 w-5 text-slate-400" />
            {notificationItems.filter(n => !n.is_read).length > 0 && (
              <span className="absolute top-1 right-1 h-3 w-3 rounded-full bg-brand-500 animate-pulse" />
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 glass border border-slate-800 rounded-2xl shadow-xl z-50 p-4 space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                <span className="font-bold text-sm text-slate-200">Alert Center</span>
                <span className="text-[10px] text-brand-400 font-bold uppercase">
                  {notificationItems.filter(n => !n.is_read).length} New
                </span>
              </div>
              <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                {notificationItems.length > 0 ? (
                  notificationItems.map(n => (
                    <div 
                      key={n.id} 
                      onClick={() => handleMarkNotificationRead(n.id)}
                      className={`p-3 rounded-xl border text-left cursor-pointer transition ${n.is_read ? 'bg-slate-950/40 border-slate-900 text-slate-400' : 'bg-brand-500/10 border-brand-500/20 text-slate-200 hover:bg-brand-500/20'}`}
                    >
                      <p className="text-xs font-bold">{n.title}</p>
                      <p className="text-[11px] text-slate-400 mt-1">{n.content}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 text-center py-4">No recent notifications</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Gamification Welcome Panel */}
      <div className="relative glass p-8 rounded-3xl overflow-hidden border border-brand-500/20">
        <div className="absolute top-0 right-0 w-80 h-80 bg-brand-500/10 rounded-full blur-[60px] -mr-20 -mt-20 pointer-events-none" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-xl">
            <h2 className="text-2xl font-extrabold text-white">Welcome back, {user?.full_name || 'Student'}!</h2>
            <p className="text-slate-400 text-sm md:text-base leading-relaxed">
              You currently have <span className="text-brand-400 font-bold">{user?.points || 0} Points</span>. Keep completing quizzes, reading notes, and submitting assignments to top the leaderboard!
            </p>
          </div>
          
          {/* Streak Flame & points badge */}
          <div className="flex gap-4 shrink-0">
            <div className="glass px-5 py-4 rounded-2xl border border-orange-500/30 flex items-center space-x-3 bg-orange-500/5">
              <Flame className="h-8 w-8 text-orange-500 animate-bounce" />
              <div>
                <p className="text-xs text-slate-400">Streak</p>
                <p className="text-lg font-extrabold text-white">{user?.streak_days || 0} Days</p>
              </div>
            </div>
            <div className="glass px-5 py-4 rounded-2xl border border-brand-500/30 flex items-center space-x-3 bg-brand-500/5">
              <Award className="h-8 w-8 text-brand-400" />
              <div>
                <p className="text-xs text-slate-400">Rewards</p>
                <p className="text-lg font-extrabold text-white">{user?.points || 0} XP</p>
              </div>
            </div>
          </div>
        </div>

        {/* Milestones & Badges Carousel */}
        {user?.badges && user.badges.length > 0 && (
          <div className="relative mt-6 pt-6 border-t border-slate-800/80">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Earned Achievements</p>
            <div className="flex gap-3 flex-wrap">
              {user.badges.map(b => {
                let badgeLabel = b;
                let badgeStyle = "bg-slate-900 border-slate-800 text-slate-400";
                
                if (b === "first_quiz") {
                  badgeLabel = "🎓 First Step";
                  badgeStyle = "bg-amber-500/10 border-amber-500/30 text-amber-300";
                } else if (b === "points_100") {
                  badgeLabel = "🔥 Century Mark";
                  badgeStyle = "bg-indigo-500/10 border-indigo-500/30 text-indigo-300";
                } else if (b === "points_500") {
                  badgeLabel = "💎 Grand Scholar";
                  badgeStyle = "bg-emerald-500/10 border-emerald-500/30 text-emerald-300";
                } else if (b === "streak_3") {
                  badgeLabel = "⚡ Fast Learner";
                  badgeStyle = "bg-rose-500/10 border-rose-500/30 text-rose-300";
                }
                
                return (
                  <span key={b} className={`text-xs px-3 py-1.5 rounded-full border font-bold ${badgeStyle}`}>
                    {badgeLabel}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
            <Flame className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Current Streak</p>
            <p className="text-2xl font-bold text-slate-100">{user?.streak_days || 0} Days</p>
          </div>
        </div>

        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
            <Hourglass className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Study XP</p>
            <p className="text-2xl font-bold text-slate-100">{user?.points || 0} XP</p>
          </div>
        </div>

        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Target className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Avg Accuracies</p>
            <p className="text-2xl font-bold text-slate-100">{metrics.average_quiz_score}%</p>
          </div>
        </div>

        <div className="glass p-6 rounded-2xl flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Trophy className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Completed Courses</p>
            <p className="text-2xl font-bold text-slate-100">{metrics.completed_courses}</p>
          </div>
        </div>
      </div>

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Columns - Study Materials & Submissions */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Assignments Panel */}
          <div className="glass p-6 rounded-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-brand-400" />
              <span>LMS Assignments & Deadlines</span>
            </h3>
            
            <div className="space-y-3">
              {assignmentItems.length > 0 ? (
                assignmentItems.map(a => (
                  <div key={a.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="text-sm font-bold text-slate-200">{a.title}</h4>
                        {a.submission_status === 'graded' && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold">
                            Graded: {a.marks}/100
                          </span>
                        )}
                        {a.submission_status === 'submitted' && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400 font-bold">
                            Pending Review
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">{a.description}</p>
                      <p className="text-[10px] text-red-400 font-semibold flex items-center gap-1">
                        <span>Deadline: {new Date(a.deadline).toLocaleDateString()} {new Date(a.deadline).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                      </p>
                      {a.feedback && (
                        <div className="mt-2 p-2 rounded bg-slate-900 border border-slate-800 text-[11px] text-brand-300">
                          <strong>Feedback:</strong> {a.feedback}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      {a.file_url && (
                        <a 
                          href={a.file_url} 
                          target="_blank" 
                          rel="noreferrer"
                          className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:text-white text-slate-400 transition"
                          title="Download Assignment Sheet"
                        >
                          <Download className="h-4 w-4" />
                        </a>
                      )}
                      {a.submission_status !== 'graded' && (
                        <button 
                          onClick={() => setSelectedAssignment(a)}
                          className="px-4 py-2 text-xs font-bold bg-brand-500 hover:bg-brand-600 text-white rounded-lg transition cursor-pointer"
                        >
                          {a.submission_status === 'submitted' ? 'Resubmit' : 'Submit'}
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 py-4 text-center">No assignments published yet.</p>
              )}
            </div>
          </div>

          {/* Shared LMS Study Notes */}
          <div className="glass p-6 rounded-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-indigo-400" />
              <span>Shared LMS Study Notes</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {notesItems.length > 0 ? (
                notesItems.map(n => (
                  <div key={n.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-900 flex justify-between items-start gap-3">
                    <div className="space-y-1">
                      <span className="text-[9px] uppercase font-bold text-indigo-400 px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20">
                        {n.subject}
                      </span>
                      <h4 className="text-sm font-bold text-slate-200 mt-2">{n.title}</h4>
                      <p className="text-xs text-slate-400 leading-normal line-clamp-2">{n.description}</p>
                    </div>

                    <a 
                      href={n.file_url} 
                      target="_blank" 
                      rel="noreferrer"
                      className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:text-white text-slate-400 transition shrink-0 mt-1"
                      title="Download Study Sheet"
                    >
                      <Download className="h-4 w-4" />
                    </a>
                  </div>
                ))
              ) : (
                <div className="col-span-2 text-center text-slate-500 py-4 text-xs">No shared study notes found.</div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column - Recommendations & AI Tutor Quick Links */}
        <div className="space-y-8">
          
          {/* Personalized Path */}
          <div className="glass p-6 rounded-2xl flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100">Personalized Paths</h3>
              <span className="text-[10px] uppercase font-bold text-brand-400 px-2 py-1 rounded bg-brand-500/10 border border-brand-500/20">
                AI Twin engine
              </span>
            </div>

            <div className="flex-1 flex flex-col justify-center space-y-4">
              {recommendationItems.length > 0 ? (
                recommendationItems.map((rec) => (
                  <div key={rec.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3 hover:border-brand-500/30 transition duration-200">
                    <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400 shrink-0">
                      <BookOpen className="h-4.5 w-4.5" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="text-sm font-bold text-slate-200 leading-snug">{rec.target_title}</h4>
                      <p className="text-xs text-slate-400 leading-normal">{rec.reason}</p>
                      <div className="pt-2 flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-bold">Match: {rec.relevance_score}%</span>
                        <Link to={`/courses/${rec.target_id}`} className="text-[10px] text-brand-400 font-bold flex items-center space-x-0.5 hover:underline">
                          <span>Study Course</span>
                          <ArrowRight className="h-3 w-3" />
                        </Link>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500 text-sm">
                  No active recommendations. Keep attempting quizzes to refine gap suggestions!
                </div>
              )}
            </div>
          </div>

          {/* Quick AI Tutor panel */}
          <div className="glass p-6 rounded-2xl border border-indigo-500/20 bg-indigo-500/5 space-y-4">
            <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wider">AI Companion Chat</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ask EduTwin questions about Python, databases, or assignments. It will suggest notes and weak quizzes to build your knowledge map.
            </p>
            <Link 
              to="/chat" 
              className="w-full py-2.5 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold rounded-xl flex items-center justify-center space-x-2 text-xs transition"
            >
              <Play className="h-4 w-4" />
              <span>Launch AI Tutor</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Assignment Submission Modal */}
      {selectedAssignment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="glass max-w-lg w-full p-6 border border-slate-800 rounded-3xl space-y-4 text-left relative">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="font-bold text-lg text-slate-200">Submit: {selectedAssignment.title}</h3>
              <button 
                onClick={() => { setSelectedAssignment(null); setErrorMsg(''); setSuccessMsg(''); setUploadedFile(null); }}
                className="text-slate-400 hover:text-white text-sm"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleSubmissionSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Submission Comments</label>
                <textarea 
                  value={submissionText}
                  onChange={(e) => setSubmissionText(e.target.value)}
                  placeholder="Type any answers or remarks here..."
                  className="w-full h-32 rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                  required
                />
              </div>

              {/* Upload File component */}
              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Attach Assignment Work (PDF, DOCX, PPT)</label>
                <div className="flex items-center space-x-3">
                  <input 
                    type="file" 
                    onChange={handleFileUpload} 
                    className="hidden" 
                    id="homework-file-picker" 
                    disabled={submitting}
                  />
                  <label 
                    htmlFor="homework-file-picker"
                    className="px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900 text-xs text-slate-300 font-bold hover:bg-slate-800 transition cursor-pointer flex items-center gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    <span>Choose file</span>
                  </label>
                  {uploadedFile && (
                    <span className="text-xs text-emerald-400 font-bold truncate max-w-[200px]">
                      {uploadedFile.file_name}
                    </span>
                  )}
                </div>
              </div>

              {errorMsg && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {successMsg && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-xl flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  <span>{successMsg}</span>
                </div>
              )}

              <button 
                type="submit"
                disabled={submitting}
                className="w-full py-3 bg-brand-500 hover:bg-brand-600 text-white font-bold rounded-xl transition text-sm flex items-center justify-center space-x-2"
              >
                {submitting ? 'Processing...' : 'Submit Work'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
