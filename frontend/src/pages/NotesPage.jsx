import React, { useEffect, useState } from 'react';
import { StickyNote, Search, Trash2, Edit3, Sparkles } from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const NotesPage = () => {
  const { data: notes, loading, error, call: fetchNotes } = useApi(() => api.get('/users/me/notes/search?q='));
  const [searchTerm, setSearchTerm] = useState('');
  const [activeNote, setActiveNote] = useState(null);
  const [editingContent, setEditingContent] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchNotes();
  }, []);

  const handleSelectNote = (note) => {
    setActiveNote(note);
    setEditingContent(note.content);
  };

  const handleSaveNote = async () => {
    if (!activeNote) return;
    setSaving(true);
    try {
      const res = await api.put(`/notes/${activeNote.id}`, { content: editingContent });
      // Update local state
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

  const filteredNotes = (notes || []).filter(note => 
    note.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Your Study Journal</h1>
        <p className="text-slate-400 text-sm mt-1">Review summaries and edit compiled lesson notes</p>
      </div>

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
    </div>
  );
};

export default NotesPage;
