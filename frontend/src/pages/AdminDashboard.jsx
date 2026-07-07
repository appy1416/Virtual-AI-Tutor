import React, { useEffect, useState } from 'react';
import { 
  Shield, 
  Users, 
  Award, 
  ShieldAlert, 
  CheckCircle, 
  Search, 
  RefreshCw, 
  BookOpen, 
  Activity, 
  FileText, 
  Upload, 
  PlusCircle, 
  Trash2, 
  Eye, 
  Clock, 
  FileSpreadsheet,
  Check
} from 'lucide-react';
import api, { getFileUrl } from '../config/api';
import { useApi } from '../hooks/useApi';

// Chart.js imports
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');

  // API Call hooks
  const { data: usersData, loading: loadingUsers, call: fetchUsers } = useApi(() => api.get('/admin/users'));
  const { data: statsData, call: fetchStats } = useApi(() => api.get('/admin/stats'));
  const { data: activityLogs, call: fetchLogs } = useApi(() => api.get('/admin/activity-logs?limit=50'));
  const { data: assignments, call: fetchAssignments } = useApi(() => api.get('/assignments'));
  const { data: sharedNotes, call: fetchSharedNotes } = useApi(() => api.get('/lms-notes'));

  // State Management
  const [searchTerm, setSearchTerm] = useState('');
  const [updatingUserId, setUpdatingUserId] = useState(null);

  // Forms State
  // 1. Study Notes
  const [noteTitle, setNoteTitle] = useState('');
  const [noteDesc, setNoteDesc] = useState('');
  const [noteSubject, setNoteSubject] = useState('');
  const [uploadedNoteFile, setUploadedNoteFile] = useState(null);

  // 2. Assignments
  const [assignTitle, setAssignTitle] = useState('');
  const [assignDesc, setAssignDesc] = useState('');
  const [assignDeadline, setAssignDeadline] = useState('');
  const [uploadedAssignFile, setUploadedAssignFile] = useState(null);

  // 3. Grading
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [gradeMarks, setGradeMarks] = useState(100);
  const [gradeFeedback, setGradeFeedback] = useState('');

  // 4. Submissions List Drawer
  const [activeAssignmentSubmissions, setActiveAssignmentSubmissions] = useState([]);
  const [selectedAssignForSubs, setSelectedAssignForSubs] = useState(null);

  // Status logs
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchUsers();
    fetchStats();
    fetchLogs();
    fetchAssignments();
    fetchSharedNotes();
  }, []);

  const handleToggleRole = async (userId, currentRole) => {
    setUpdatingUserId(userId);
    const newRole = currentRole === 'student' ? 'tutor' : 'student';
    try {
      await api.put(`/admin/users/${userId}/role`, { role: newRole });
      fetchUsers();
      fetchStats();
    } catch (e) {
      alert('Failed to update user role.');
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleToggleSuspension = async (userId, isDeactivated) => {
    setUpdatingUserId(userId);
    try {
      if (isDeactivated) {
        await api.post(`/admin/users/${userId}/reactivate`);
      } else {
        await api.post(`/admin/users/${userId}/deactivate`);
      }
      fetchUsers();
      fetchStats();
    } catch (e) {
      alert('Failed to modify user suspension state.');
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to permanently delete this user?')) return;
    setUpdatingUserId(userId);
    try {
      await api.delete(`/admin/users/${userId}`);
      fetchUsers();
      fetchStats();
    } catch (e) {
      alert('Failed to delete user.');
    } finally {
      setUpdatingUserId(null);
    }
  };

  // General File Upload Helper
  const handleFileUpload = async (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setSubmitting(true);
      setErrorMsg('');
      const res = await api.post('/assignments/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data?.success) {
        if (type === 'note') {
          setUploadedNoteFile(res.data.data);
        } else {
          setUploadedAssignFile(res.data.data);
        }
        setSuccessMsg('File uploaded successfully!');
      } else {
        setErrorMsg('File upload failed.');
      }
    } catch (err) {
      setErrorMsg('File upload error: ' + (err.response?.data?.message || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  // Publish Shared Note
  const handlePublishNote = async (e) => {
    e.preventDefault();
    if (!uploadedNoteFile) {
      setErrorMsg('Please upload a PDF/DOCX/PPT file first.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg('');
      setSuccessMsg('');

      const res = await api.post('/lms-notes', {
        title: noteTitle,
        description: noteDesc,
        subject: noteSubject,
        file_name: uploadedNoteFile.file_name,
        file_url: uploadedNoteFile.file_url,
        file_type: uploadedNoteFile.file_name.split('.').pop() || 'pdf'
      });

      if (res.data?.success) {
        setSuccessMsg('Note published successfully!');
        setNoteTitle('');
        setNoteDesc('');
        setNoteSubject('');
        setUploadedNoteFile(null);
        fetchSharedNotes();
        fetchStats();
      }
    } catch (err) {
      setErrorMsg('Publish error: ' + (err.response?.data?.message || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  // Publish Assignment
  const handlePublishAssignment = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setErrorMsg('');
      setSuccessMsg('');

      const res = await api.post('/assignments', {
        title: assignTitle,
        description: assignDesc,
        deadline: new Date(assignDeadline).toISOString(),
        file_url: uploadedAssignFile?.file_url || ''
      });

      if (res.data?.success) {
        setSuccessMsg('Assignment published successfully!');
        setAssignTitle('');
        setAssignDesc('');
        setAssignDeadline('');
        setUploadedAssignFile(null);
        fetchAssignments();
        fetchStats();
      }
    } catch (err) {
      setErrorMsg('Publish error: ' + (err.response?.data?.message || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  // Load Submissions
  const handleLoadSubmissions = async (assignment) => {
    try {
      setSelectedAssignForSubs(assignment);
      const res = await api.get(`/assignments/${assignment.id}/submissions`);
      if (res.data?.success) {
        setActiveAssignmentSubmissions(res.data.data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Submit Grade / Feedback
  const handleGradeSubmit = async (e) => {
    e.preventDefault();
    if (!selectedSubmission) return;

    try {
      setSubmitting(true);
      setErrorMsg('');
      setSuccessMsg('');

      const res = await api.post(`/submissions/${selectedSubmission.id}/grade`, {
        marks: parseInt(gradeMarks),
        feedback: gradeFeedback
      });

      if (res.data?.success) {
        setSuccessMsg('Grade submitted successfully!');
        setSelectedSubmission(null);
        setGradeFeedback('');
        // Refresh submissions list
        handleLoadSubmissions(selectedAssignForSubs);
      }
    } catch (err) {
      setErrorMsg('Grading error: ' + (err.response?.data?.message || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveNote = async (id) => {
    if (!window.confirm('Delete this study note?')) return;
    try {
      await api.delete(`/lms-notes/${id}`);
      fetchSharedNotes();
      fetchStats();
    } catch (err) {
      alert('Failed to delete note');
    }
  };

  const handleRemoveAssignment = async (id) => {
    if (!window.confirm('Delete this assignment?')) return;
    try {
      await api.delete(`/assignments/${id}`);
      fetchAssignments();
      fetchStats();
    } catch (err) {
      alert('Failed to delete assignment');
    }
  };

  const usersList = usersData?.items || usersData?.users || [];
  const totalCount = statsData?.total_users || usersList.length;

  const filteredUsers = usersList.filter(user => 
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Charts data configurations
  const barChartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Active Users Count',
        data: [2, 5, 8, 12, 9, 6, statsData?.active_students_today || 4],
        backgroundColor: 'rgba(99, 102, 241, 0.4)',
        borderColor: 'rgba(99, 102, 241, 1)',
        borderWidth: 1,
        borderRadius: 6
      }
    ]
  };

  const lineChartData = {
    labels: ['Quiz 1', 'Quiz 2', 'Quiz 3', 'Quiz 4', 'Quiz 5'],
    datasets: [
      {
        label: 'Avg Class Accuracies (%)',
        data: [75, 78, statsData?.overall_progress || 82, 85, 88],
        fill: true,
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        borderColor: '#6366f1',
        tension: 0.4
      }
    ]
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center space-x-2 text-white">
            <Shield className="h-8 w-8 text-brand-400" />
            <span>Admin Control Suite</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">Manage user access control, publish learning materials, and grade assignments</p>
        </div>
      </div>

      {/* Navigation tabs */}
      <div className="flex space-x-2 border-b border-slate-800 pb-px">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'users', label: 'User Directory', icon: Users },
          { id: 'notes', label: 'Study Notes', icon: BookOpen },
          { id: 'assignments', label: 'Assignments', icon: FileText },
          { id: 'logs', label: 'Audit Logs', icon: Clock }
        ].map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setErrorMsg(''); setSuccessMsg(''); }}
              className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-bold transition rounded-t-xl cursor-pointer ${activeTab === tab.id ? 'bg-slate-900 border-t-2 border-brand-500 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-900/40'}`}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* 1. OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div className="space-y-8 animate-fade-in">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="glass p-6 rounded-2xl flex items-center space-x-4">
              <div className="p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs text-slate-500 font-semibold block uppercase">Total Students</span>
                <span className="text-2xl font-bold text-slate-100">{statsData?.total_students ?? 0}</span>
              </div>
            </div>

            <div className="glass p-6 rounded-2xl flex items-center space-x-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <Activity className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs text-slate-500 font-semibold block uppercase">Active Today</span>
                <span className="text-2xl font-bold text-slate-100">{statsData?.active_students_today ?? 0} Active</span>
              </div>
            </div>

            <div className="glass p-6 rounded-2xl flex items-center space-x-4">
              <div className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
                <FileSpreadsheet className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs text-slate-500 font-semibold block uppercase">LMS Quizzes & Notes</span>
                <span className="text-2xl font-bold text-slate-100">{(statsData?.total_quizzes ?? 0) + (statsData?.total_study_notes ?? 0)}</span>
              </div>
            </div>

            <div className="glass p-6 rounded-2xl flex items-center space-x-4">
              <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Award className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs text-slate-500 font-semibold block uppercase">Avg Class Accuracy</span>
                <span className="text-2xl font-bold text-slate-100">{statsData?.overall_progress ?? 80}%</span>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="glass p-6 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Weekly Daily Active Users (DAU)</h3>
              <div className="h-64 flex justify-center">
                <Bar data={barChartData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
            <div className="glass p-6 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Overall Learning Progress Curve</h3>
              <div className="h-64 flex justify-center">
                <Line data={lineChartData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. USERS TAB */}
      {activeTab === 'users' && (
        <div className="glass rounded-2xl border border-slate-800 overflow-hidden animate-fade-in">
          <div className="p-4 border-b border-slate-900 bg-slate-900/40 flex items-center justify-between gap-4">
            <div className="relative w-full max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-850 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            {loadingUsers ? (
              <div className="flex h-48 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
              </div>
            ) : filteredUsers.length > 0 ? (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-900 bg-slate-900/20 text-slate-400 font-bold uppercase tracking-wider">
                    <th className="p-4">Full Name</th>
                    <th className="p-4">Email</th>
                    <th className="p-4">Role</th>
                    <th className="p-4">Points</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900/60">
                  {filteredUsers.map((user) => {
                    const isDeactivated = !user.is_active;
                    return (
                      <tr key={user.id} className="hover:bg-slate-900/20 text-slate-300">
                        <td className="p-4 font-bold text-slate-200">{user.full_name}</td>
                        <td className="p-4 text-slate-400">{user.email}</td>
                        <td className="p-4">
                          <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] uppercase border ${user.role === 'admin' ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'}`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="p-4 font-extrabold text-brand-400">{user.points || 0} XP</td>
                        <td className="p-4">
                          <span className={`flex items-center space-x-1 ${isDeactivated ? 'text-red-400' : 'text-emerald-400'}`}>
                            {isDeactivated ? <ShieldAlert className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
                            <span className="font-bold">{isDeactivated ? 'Suspended' : 'Active'}</span>
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex justify-end items-center space-x-2">
                            <button
                              onClick={() => handleToggleRole(user.id, user.role)}
                              disabled={updatingUserId === user.id || user.role === 'admin'}
                              className="px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 font-bold transition disabled:opacity-50 cursor-pointer text-slate-300"
                            >
                              Toggle Role
                            </button>
                            <button
                              onClick={() => handleToggleSuspension(user.id, isDeactivated)}
                              disabled={updatingUserId === user.id || user.role === 'admin'}
                              className={`px-2.5 py-1.5 rounded-lg font-bold transition disabled:opacity-50 cursor-pointer ${isDeactivated ? 'bg-emerald-650/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-650' : 'bg-red-650/10 border border-red-500/20 text-red-400 hover:bg-red-650'}`}
                            >
                              {isDeactivated ? 'Reactivate' : 'Suspend'}
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              disabled={updatingUserId === user.id || user.role === 'admin'}
                              className="p-2 rounded-lg bg-red-500/10 border border-red-500/20 hover:bg-red-500 text-red-400 hover:text-white transition disabled:opacity-50 cursor-pointer"
                              title="Delete Account"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-12 text-slate-500 text-sm">No users registered on the platform.</div>
            )}
          </div>
        </div>
      )}

      {/* 3. STUDY NOTES TAB */}
      {activeTab === 'notes' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-fade-in">
          {/* Notes publisher form */}
          <div className="glass p-6 rounded-2xl border border-slate-800 space-y-4 h-fit">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <PlusCircle className="h-5 w-5 text-brand-400" />
              <span>Publish Note</span>
            </h3>
            
            <form onSubmit={handlePublishNote} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Note Title</label>
                <input 
                  type="text"
                  value={noteTitle}
                  onChange={(e) => setNoteTitle(e.target.value)}
                  placeholder="e.g. Intro to NumPy"
                  className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Description</label>
                <textarea 
                  value={noteDesc}
                  onChange={(e) => setNoteDesc(e.target.value)}
                  placeholder="Brief note overview..."
                  className="w-full h-24 rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Subject / Topic Category</label>
                <input 
                  type="text"
                  value={noteSubject}
                  onChange={(e) => setNoteSubject(e.target.value)}
                  placeholder="e.g. Science, Math"
                  className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                  required
                />
              </div>

              {/* Note PDF Picker */}
              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Upload Note Document (PDF, DOCX, PPT)</label>
                <div className="flex items-center space-x-3">
                  <input 
                    type="file" 
                    onChange={(e) => handleFileUpload(e, 'note')} 
                    className="hidden" 
                    id="admin-note-picker"
                    disabled={submitting}
                  />
                  <label 
                    htmlFor="admin-note-picker"
                    className="px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900 text-xs text-slate-300 font-bold hover:bg-slate-800 transition cursor-pointer flex items-center gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    <span>Choose File</span>
                  </label>
                  {uploadedNoteFile && (
                    <span className="text-xs text-emerald-400 font-bold truncate max-w-[150px]">
                      {uploadedNoteFile.file_name}
                    </span>
                  )}
                </div>
              </div>

              {errorMsg && <p className="text-xs text-red-400 font-bold">{errorMsg}</p>}
              {successMsg && <p className="text-xs text-emerald-400 font-bold">{successMsg}</p>}

              <button 
                type="submit"
                disabled={submitting}
                className="w-full py-3 bg-brand-500 hover:bg-brand-600 text-white font-bold rounded-xl text-xs transition flex items-center justify-center space-x-2"
              >
                {submitting ? 'Processing...' : 'Publish Study Note'}
              </button>
            </form>
          </div>

          {/* Published Notes list */}
          <div className="lg:col-span-2 glass p-6 rounded-2xl border border-slate-800 space-y-4">
            <h3 className="text-lg font-bold text-slate-100">Active Study Notes</h3>
            <div className="space-y-3">
              {sharedNotes && sharedNotes.length > 0 ? (
                sharedNotes.map(n => (
                  <div key={n.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-900 flex items-center justify-between gap-4">
                    <div>
                      <span className="text-[9px] uppercase font-bold text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
                        {n.subject}
                      </span>
                      <h4 className="text-sm font-bold text-slate-200 mt-2">{n.title}</h4>
                      <p className="text-xs text-slate-400 leading-normal">{n.description}</p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <a 
                        href={getFileUrl(n.file_url)} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="p-2 border border-slate-800 hover:text-white rounded-lg transition"
                      >
                        <Eye className="h-4 w-4 text-slate-400" />
                      </a>
                      <button 
                        onClick={() => handleRemoveNote(n.id)}
                        className="p-2 border border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white rounded-lg transition cursor-pointer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 py-6 text-center">No study notes uploaded.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 4. ASSIGNMENTS TAB */}
      {activeTab === 'assignments' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-fade-in">
          {/* Assignment publisher form */}
          <div className="glass p-6 rounded-2xl border border-slate-800 space-y-4 h-fit">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <PlusCircle className="h-5 w-5 text-brand-400" />
              <span>Create Assignment</span>
            </h3>
            
            <form onSubmit={handlePublishAssignment} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Assignment Title</label>
                <input 
                  type="text"
                  value={assignTitle}
                  onChange={(e) => setAssignTitle(e.target.value)}
                  placeholder="e.g. Midterm Homework"
                  className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Instructions</label>
                <textarea 
                  value={assignDesc}
                  onChange={(e) => setAssignDesc(e.target.value)}
                  placeholder="Assignment guidelines..."
                  className="w-full h-24 rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Deadline Date</label>
                <input 
                  type="datetime-local"
                  value={assignDeadline}
                  onChange={(e) => setAssignDeadline(e.target.value)}
                  className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                  required
                />
              </div>

              {/* Assignment PDF Picker */}
              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-bold block">Attach Assignment Work Sheet (Optional)</label>
                <div className="flex items-center space-x-3">
                  <input 
                    type="file" 
                    onChange={(e) => handleFileUpload(e, 'assign')} 
                    className="hidden" 
                    id="admin-assign-picker"
                    disabled={submitting}
                  />
                  <label 
                    htmlFor="admin-assign-picker"
                    className="px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900 text-xs text-slate-300 font-bold hover:bg-slate-800 transition cursor-pointer flex items-center gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    <span>Choose File</span>
                  </label>
                  {uploadedAssignFile && (
                    <span className="text-xs text-emerald-400 font-bold truncate max-w-[150px]">
                      {uploadedAssignFile.file_name}
                    </span>
                  )}
                </div>
              </div>

              {errorMsg && <p className="text-xs text-red-400 font-bold">{errorMsg}</p>}
              {successMsg && <p className="text-xs text-emerald-400 font-bold">{successMsg}</p>}

              <button 
                type="submit"
                disabled={submitting}
                className="w-full py-3 bg-brand-500 hover:bg-brand-600 text-white font-bold rounded-xl text-xs transition flex items-center justify-center space-x-2"
              >
                {submitting ? 'Processing...' : 'Create Assignment'}
              </button>
            </form>
          </div>

          {/* List assignments & submissions */}
          <div className="lg:col-span-2 space-y-8">
            <div className="glass p-6 rounded-2xl border border-slate-800 space-y-4">
              <h3 className="text-lg font-bold text-slate-100">Assignments & Submissions Review</h3>
              
              <div className="space-y-3">
                {assignments && assignments.length > 0 ? (
                  assignments.map(a => (
                    <div key={a.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <h4 className="text-sm font-bold text-slate-200">{a.title}</h4>
                        <p className="text-xs text-slate-400 leading-normal">{a.description}</p>
                        <p className="text-[10px] text-slate-500 font-semibold mt-1">Deadline: {new Date(a.deadline).toLocaleDateString()}</p>
                      </div>

                      <div className="flex items-center space-x-2 shrink-0">
                        <button 
                          onClick={() => handleLoadSubmissions(a)}
                          className="px-3 py-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold text-xs rounded-lg transition hover:bg-indigo-500 hover:text-white cursor-pointer"
                        >
                          View Submissions
                        </button>
                        <button 
                          onClick={() => handleRemoveAssignment(a.id)}
                          className="p-2 border border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white rounded-lg transition cursor-pointer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 py-6 text-center">No assignments published.</p>
                )}
              </div>
            </div>

            {/* Submissions list drawer */}
            {selectedAssignForSubs && (
              <div className="glass p-6 rounded-2xl border border-slate-850 space-y-4">
                <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                  <h4 className="font-bold text-sm text-slate-200">Submissions for: {selectedAssignForSubs.title}</h4>
                  <button 
                    onClick={() => { setSelectedAssignForSubs(null); setActiveAssignmentSubmissions([]); setSelectedSubmission(null); }}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Close
                  </button>
                </div>

                <div className="space-y-3">
                  {activeAssignmentSubmissions.length > 0 ? (
                    activeAssignmentSubmissions.map(s => (
                      <div key={s.id} className="p-4 rounded-xl bg-slate-900 border border-slate-850 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-1">
                          <p className="text-xs font-bold text-slate-200">{s.student_name} ({s.student_email})</p>
                          <p className="text-xs text-slate-400 leading-normal mt-1">{s.submission_text}</p>
                          {s.file_url && (
                            <a 
                              href={getFileUrl(s.file_url)} 
                              target="_blank" 
                              rel="noreferrer"
                              className="text-[11px] text-brand-400 font-bold hover:underline flex items-center space-x-1 mt-1"
                            >
                              <span>Attached: {s.file_name}</span>
                            </a>
                          )}
                          {s.marks !== null && (
                            <p className="text-[10px] text-emerald-400 font-bold mt-1">Graded: {s.marks}/100 - Feedback: {s.feedback}</p>
                          )}
                        </div>

                        <button 
                          onClick={() => setSelectedSubmission(s)}
                          className="px-3 py-1.5 bg-brand-500 text-white font-bold text-xs rounded-lg hover:bg-brand-600 transition shrink-0 cursor-pointer"
                        >
                          {s.marks !== null ? 'Re-grade' : 'Grade'}
                        </button>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 text-center py-4">No submissions received yet.</p>
                  )}
                </div>
              </div>
            )}

            {/* Grading Form Modal */}
            {selectedSubmission && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
                <div className="glass max-w-md w-full p-6 border border-slate-800 rounded-3xl space-y-4 text-left">
                  <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                    <h4 className="font-bold text-sm text-slate-200">Grade Student Submission</h4>
                    <button 
                      onClick={() => { setSelectedSubmission(null); setErrorMsg(''); setSuccessMsg(''); }}
                      className="text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                  </div>

                  <form onSubmit={handleGradeSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-xs text-slate-400 font-bold block">Marks / Score (0-100)</label>
                      <input 
                        type="number" 
                        min="0" 
                        max="100"
                        value={gradeMarks}
                        onChange={(e) => setGradeMarks(e.target.value)}
                        className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-xs text-slate-400 font-bold block">Feedback Comments</label>
                      <textarea 
                        value={gradeFeedback}
                        onChange={(e) => setGradeFeedback(e.target.value)}
                        placeholder="Add review remarks..."
                        className="w-full h-24 rounded-xl bg-slate-900 border border-slate-800 p-3 text-slate-200 text-sm focus:border-brand-500 focus:outline-none"
                        required
                      />
                    </div>

                    {errorMsg && <p className="text-xs text-red-400 font-bold">{errorMsg}</p>}
                    {successMsg && <p className="text-xs text-emerald-400 font-bold">{successMsg}</p>}

                    <button 
                      type="submit"
                      disabled={submitting}
                      className="w-full py-3 bg-brand-500 hover:bg-brand-600 text-white font-bold rounded-xl text-xs transition"
                    >
                      {submitting ? 'Submitting...' : 'Submit Grade'}
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. AUDIT LOGS TAB */}
      {activeTab === 'logs' && (
        <div className="glass rounded-2xl border border-slate-800 overflow-hidden animate-fade-in">
          <div className="p-4 border-b border-slate-900 bg-slate-900/40">
            <h3 className="font-bold text-sm text-slate-200">Security Audit Logs</h3>
          </div>
          <div className="overflow-x-auto">
            {activityLogs && activityLogs.length > 0 ? (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-900 bg-slate-900/20 text-slate-400 font-bold uppercase tracking-wider">
                    <th className="p-4">User</th>
                    <th className="p-4">Action</th>
                    <th className="p-4">Description</th>
                    <th className="p-4">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900/60">
                  {activityLogs.map(l => (
                    <tr key={l.id} className="hover:bg-slate-900/10 text-slate-300">
                      <td className="p-4 font-bold text-slate-200">
                        <div>{l.user_name}</div>
                        <div className="text-[10px] text-slate-500 font-normal">{l.user_email}</div>
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                          l.action_type === 'login' ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' :
                          l.action_type === 'quiz_attempt' ? 'bg-orange-500/10 border-orange-500/20 text-orange-400' :
                          l.action_type === 'submit_assignment' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                          'bg-slate-800 border-slate-700 text-slate-400'
                        }`}>
                          {l.action_type}
                        </span>
                      </td>
                      <td className="p-4 text-slate-400 max-w-sm truncate">{l.description}</td>
                      <td className="p-4 text-slate-500 font-semibold">{new Date(l.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-xs text-slate-500 text-center py-8">No security logs recorded.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
