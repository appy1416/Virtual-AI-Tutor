import React, { useEffect, useState } from 'react';
import { StickyNote, Search, Trash2, Edit3, Sparkles, Download, FileText, Calendar, Eye } from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const NotesPage = () => {
  const [activeTab, setActiveTab] = useState('journal'); // 'journal' or 'shared'
  
  // My Journal Notes State
  const { data: notes, loading, error, call: fetchNotes } = useApi(() => api.get('/users/me/notes/search?q='));
  const [searchTerm, setSearchTerm] = useState('');
  const [activeNote, setActiveNote] = useState(null);
  const [editingContent, setEditingContent] = useState('');
  const [saving, setSaving] = useState(false);

  // Shared Class Materials State
  const { data: sharedNotes, loading: loadingShared, call: fetchSharedNotes } = useApi(() => api.get('/lms-notes'));
  const [searchSharedTerm, setSearchSharedTerm] = useState('');

  useEffect(() => {
    if (activeTab === 'journal') {
      fetchNotes();
    } else {
      fetchSharedNotes();
    }
  }, [activeTab]);

  const handleSelectNote = (note) => {
    setActiveNote(note);
    setEditingContent(note.content);
  };

  const handleSaveNote = async () => {
    if (!activeNote) return;
    setSaving(true);
    try {
      const res = await api.put(`/notes/${activeNote.id}`, { content: editingContent });
      const updated = res.data.data;
      setActiveNote(updated);
      fetchNotes();
    } catch (e) {
      // Ignored
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!window.confirm('Delete this note?')) return;
    try {
      await api.delete(`/notes/${noteId}`);
      if (activeNote?.id === noteId) {
        setActiveNote(null);
      }
      fetchNotes();
    } catch (e) {
      // Ignored
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredNotes = (notes || []).filter(note => 
    note.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredSharedNotes = (sharedNotes || []).filter(note => 
    note.title.toLowerCase().includes(searchSharedTerm.toLowerCase()) ||
    note.subject.toLowerCase().includes(searchSharedTerm.toLowerCase()) ||
    note.description.toLowerCase().includes(searchSharedTerm.toLowerCase())
  );

  // Resolve base API URL to point directly to secure download endpoints
  const getDownloadUrl = (noteId) => {
    const base = api.defaults.baseURL || 'https://virtual-ai-tutor-tqet.onrender.com/api/v1';
    return `${base}/lms-notes/${noteId}/file`;
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Study Journals & Notes</h1>
          <p className="text-slate-400 text-sm mt-1">Access your drafts, review notes, and download course handouts</p>
        </div>

        {/* Tab Selection */}
        <div className="flex rounded-xl p-1 bg-slate-900 border border-slate-800 self-start">
          <button
            onClick={() => setActiveTab('journal')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition cursor-pointer ${
              activeTab === 'journal' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            My Journal Notes
          </button>
          <button
            onClick={() => setActiveTab('shared')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition cursor-pointer ${
              activeTab === 'shared' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Shared Class Notes
          </button>
        </div>
      </div>

      {activeTab === 'journal' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Left Side: Note List */}
          <div className="space-y-4 md:col-span-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search notes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
              />
            </div>

            <div className="space-y-2 h-[450px] overflow-y-auto pr-1">
              {loading ? (
                <div className="flex h-32 items-center justify-center">
                  <div className="h-6 w-6 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
                </div>
              ) : filteredNotes.length > 0 ? (
                filteredNotes.map((note) => (
                  <div 
                    key={note.id}
                    onClick={() => handleSelectNote(note)}
                    className={`p-4 rounded-xl border text-left cursor-pointer transition ${
                      activeNote?.id === note.id
                        ? 'bg-brand-600/10 border-brand-500'
                        : 'bg-slate-900 border-slate-850 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="text-[10px] font-bold text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 uppercase">
                        Note
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteNote(note.id);
                        }}
                        className="p-1 text-slate-500 hover:text-red-400 transition"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <p className="text-xs text-slate-200 mt-2 line-clamp-2 leading-relaxed">{note.content}</p>
                    <span className="text-[10px] text-slate-500 block mt-2 font-medium">Words: {note.word_count}</span>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-600 text-xs">
                  No notes found. Create notes inside lessons!
                </div>
              )}
            </div>
          </div>

          {/* Right Side: Note Editor / Viewer */}
          <div className="md:col-span-2">
            {activeNote ? (
              <div className="glass p-6 rounded-2xl border border-slate-800 space-y-6">
                <div className="flex justify-between items-center border-b border-slate-900 pb-4">
                  <div className="flex items-center space-x-2">
                    <StickyNote className="h-5 w-5 text-brand-400" />
                    <h3 className="text-sm font-bold text-slate-200">View/Edit Note Content</h3>
                  </div>

                  <button
                    onClick={handleSaveNote}
                    disabled={saving}
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-xs font-bold text-white transition disabled:opacity-50 cursor-pointer"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>

                <textarea
                  value={editingContent}
                  onChange={(e) => setEditingContent(e.target.value)}
                  className="w-full h-72 p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition leading-relaxed resize-none"
                />

                {activeNote.ai_summary && (
                  <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 space-y-2">
                    <span className="flex items-center space-x-1 text-[10px] uppercase font-bold text-indigo-400">
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>AI Compiled Summary</span>
                    </span>
                    <p className="text-xs text-slate-400 leading-relaxed italic">
                      "{activeNote.ai_summary}"
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="glass h-full flex flex-col items-center justify-center text-center p-8 rounded-2xl border border-slate-850">
                <StickyNote className="h-12 w-12 text-slate-700 mb-4" />
                <h3 className="text-sm font-bold text-slate-400">No Note Selected</h3>
                <p className="text-xs text-slate-500 mt-1">Select a note from the panel to edit details</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Shared Notes View */
        <div className="space-y-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search shared handouts by title, subject..."
              value={searchSharedTerm}
              onChange={(e) => setSearchSharedTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
            />
          </div>

          {loadingShared ? (
            <div className="flex h-32 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
            </div>
          ) : filteredSharedNotes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredSharedNotes.map((note) => (
                <div 
                  key={note.id}
                  className="glass p-5 rounded-2xl border border-slate-800 hover:border-brand-500/20 transition duration-200 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex justify-between items-start gap-2">
                      <span className="text-[9px] uppercase font-bold text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20 shrink-0">
                        {note.subject}
                      </span>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(note.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-slate-200 leading-snug">{note.title}</h3>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{note.description}</p>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-900 space-y-3">
                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                      <span className="flex items-center gap-1">
                        <FileText className="h-3.5 w-3.5 text-brand-400" />
                        <span className="truncate max-w-[120px]" title={note.file_name}>{note.file_name}</span>
                      </span>
                      <span>Size: {formatBytes(note.file_size)}</span>
                    </div>
                    
                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                      <span>Downloads: <strong>{note.download_count || 0}</strong></span>
                    </div>

                    <div className="flex gap-2">
                      {note.file_type.toLowerCase() === 'pdf' && (
                        <button
                          onClick={() => window.open(getDownloadUrl(note.id), '_blank')}
                          className="flex-1 py-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-[10px] font-bold text-slate-300 hover:text-white flex items-center justify-center gap-1 transition cursor-pointer"
                        >
                          <Eye className="h-3 w-3" />
                          <span>Preview</span>
                        </button>
                      )}
                      <a
                        href={getDownloadUrl(note.id)}
                        download
                        onClick={() => setTimeout(() => fetchSharedNotes(), 1000)}
                        className="flex-1 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-[10px] font-bold text-white flex items-center justify-center gap-1 transition text-center"
                      >
                        <Download className="h-3 w-3" />
                        <span>Download</span>
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs">
              No shared class notes available.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotesPage;
