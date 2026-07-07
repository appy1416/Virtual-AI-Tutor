import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  BookOpen, 
  StickyNote, 
  MessageSquare, 
  HelpCircle, 
  CheckCircle, 
  Sparkles,
  Send,
  RefreshCw
} from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const LessonPage = () => {
  const { lessonId } = useParams();
  const { data: lesson, loading: lessonLoading, call: fetchLesson } = useApi(() => api.get(`/lessons/${lessonId}`));
  
  // Note State
  const [noteContent, setNoteContent] = useState('');
  const [noteId, setNoteId] = useState(null);
  const [noteSummary, setNoteSummary] = useState('');
  const [noteTags, setNoteTags] = useState([]);
  const [savingNote, setSavingNote] = useState(false);
  const [summarizingNote, setSummarizingNote] = useState(false);

  // Chat State
  const [chatSessionId, setChatSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sendingMsg, setSendingMsg] = useState(false);

  // Handouts State
  const [handouts, setHandouts] = useState([]);
  const [loadingHandouts, setLoadingHandouts] = useState(false);

  // Tab State: 'content', 'notes', 'chat', 'handouts'
  const [activeTab, setActiveTab] = useState('content');

  const fetchHandouts = async () => {
    setLoadingHandouts(true);
    try {
      const res = await api.get(`/lms-notes?lesson_id=${lessonId}`);
      setHandouts(res.data?.data || []);
    } catch (e) {
      // Ignored
    } finally {
      setLoadingHandouts(false);
    }
  };

  useEffect(() => {
    fetchLesson();
    fetchOrCreateNote();
    fetchOrCreateChatSession();
    fetchHandouts();
  }, [lessonId]);

  const fetchOrCreateNote = async () => {
    try {
      const res = await api.get(`/users/me/notes/search?q=`);
      const allNotes = res.data?.data || [];
      const existing = allNotes.find(n => n.lesson_id === lessonId);
      if (existing) {
        setNoteId(existing.id);
        setNoteContent(existing.content);
        setNoteSummary(existing.ai_summary || '');
        setNoteTags(existing.tags || []);
      }
    } catch (e) {
      // Ignored
    }
  };

  const handleSaveNote = async () => {
    setSavingNote(true);
    try {
      if (noteId) {
        // Update
        const res = await api.put(`/notes/${noteId}`, { content: noteContent, tags: noteTags });
        setNoteContent(res.data.data.content);
      } else {
        // Create
        const res = await api.post(`/lessons/${lessonId}/notes`, { content: noteContent });
        setNoteId(res.data.data.id);
        setNoteContent(res.data.data.content);
      }
    } catch (e) {
      // Ignored
    } finally {
      setSavingNote(false);
    }
  };

  const handleSummarizeNote = async () => {
    if (!noteId) return;
    setSummarizingNote(true);
    try {
      const res = await api.post(`/notes/${noteId}/summarize`);
      setNoteSummary(res.data.data.ai_summary);
    } catch (e) {
      // Ignored
    } finally {
      setSummarizingNote(false);
    }
  };

  const fetchOrCreateChatSession = async () => {
    try {
      const res = await api.post('/chat/start', { lesson_id: lessonId, course_id: null });
      setChatSessionId(res.data.data.id);
      setChatMessages(res.data.data.messages || []);
    } catch (e) {
      // Ignored
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !chatSessionId) return;
    const userMsg = chatInput;
    setChatInput('');
    setChatMessages(prev => [...prev, { sender: 'student', content: userMsg, timestamp: new Date().toISOString() }]);
    setSendingMsg(true);
    try {
      const res = await api.post(`/chat/${chatSessionId}/message`, { message: userMsg });
      const { user_message, ai_response } = res.data.data;
      setChatMessages(prev => [
        ...prev.filter(m => m.content !== userMsg),
        user_message,
        ai_response
      ]);
    } catch (e) {
      // Ignored
    } finally {
      setSendingMsg(false);
    }
  };

  if (lessonLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!lesson) return null;

  const objectives = Array.isArray(lesson.learning_objectives) 
    ? lesson.learning_objectives 
    : JSON.parse(lesson.learning_objectives || '[]');

  const quizzes = lesson.quizzes || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Main Content Container (2 Cols) */}
      <div className="lg:col-span-2 space-y-8">
        <div className="space-y-4">
          <Link to={`/courses/${lesson.course_id}`} className="text-xs font-bold text-brand-400 hover:underline">
            &larr; Back to Course
          </Link>
          <h1 className="text-3xl font-extrabold text-slate-100">{lesson.title}</h1>
          <p className="text-xs text-slate-400">Duration: {lesson.estimated_duration_minutes} mins</p>
        </div>

        {/* Objectives Box */}
        {objectives.length > 0 && (
          <div className="p-5 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400">Learning Objectives</h4>
            <ul className="space-y-2">
              {objectives.map((obj, i) => (
                <li key={i} className="text-xs text-slate-300 flex items-start space-x-2">
                  <CheckCircle className="h-4 w-4 text-brand-400 shrink-0 mt-0.5" />
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Markdown content container */}
        <div className="glass p-6 rounded-2xl border border-slate-800/80 leading-relaxed text-slate-300 space-y-4 text-sm whitespace-pre-line">
          {lesson.content}
        </div>

        {/* Quizzes Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <HelpCircle className="h-5 w-5 text-brand-400" />
            <span>Interactive Quizzes</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {quizzes.length > 0 ? (
              quizzes.map((quiz, i) => (
                <div key={quiz.id} className="glass p-5 rounded-2xl flex flex-col justify-between space-y-4">
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold text-brand-400 px-2 py-0.5 rounded bg-brand-500/10 uppercase">
                      Quiz {i + 1}
                    </span>
                    <h4 className="text-sm font-bold text-slate-200 line-clamp-2">{quiz.question_text}</h4>
                  </div>
                  <Link 
                    to={`/quizzes/${quiz.id}`}
                    className="w-full py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-800 text-center block transition"
                  >
                    Attempt Quiz
                  </Link>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-slate-500 text-xs col-span-2">
                No quizzes configured for this lesson.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Side Utilities (1 Col) - Notes & AI Chat Tabs */}
      <div className="space-y-6">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-900">
          <button
            onClick={() => setActiveTab('notes')}
            className={`flex-1 py-3 text-center text-xs font-bold border-b-2 transition cursor-pointer ${
              activeTab === 'notes' ? 'border-brand-500 text-brand-400' : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="inline-flex items-center space-x-1">
              <StickyNote className="h-4 w-4" />
              <span>Study Notes</span>
            </span>
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex-1 py-3 text-center text-xs font-bold border-b-2 transition cursor-pointer ${
              activeTab === 'chat' ? 'border-brand-500 text-brand-400' : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="inline-flex items-center space-x-1">
              <MessageSquare className="h-4 w-4" />
              <span>AI Tutor</span>
            </span>
          </button>
          <button
            onClick={() => setActiveTab('handouts')}
            className={`flex-1 py-3 text-center text-xs font-bold border-b-2 transition cursor-pointer ${
              activeTab === 'handouts' ? 'border-brand-500 text-brand-400' : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="inline-flex items-center space-x-1">
              <BookOpen className="h-4 w-4" />
              <span>Handouts</span>
            </span>
          </button>
        </div>

        {/* Tab Content: Notes */}
        {activeTab === 'notes' && (
          <div className="glass p-5 rounded-2xl space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Draft Lesson Notes</h4>
              <button
                onClick={handleSaveNote}
                disabled={savingNote}
                className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-[10px] font-bold text-white transition disabled:opacity-50 cursor-pointer"
              >
                {savingNote ? 'Saving...' : 'Save Note'}
              </button>
            </div>

            <textarea
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              placeholder="Write down key takeaways from this lesson in markdown..."
              className="w-full h-44 p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition resize-none"
            />

            {noteId && (
              <div className="space-y-4 pt-4 border-t border-slate-900">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-bold">AI Note Summarizer</span>
                  <button
                    onClick={handleSummarizeNote}
                    disabled={summarizingNote}
                    className="p-1.5 rounded-lg bg-brand-500/10 border border-brand-500/20 text-brand-400 hover:bg-brand-500 hover:text-white transition disabled:opacity-50 cursor-pointer"
                    title="Generate AI Summary"
                  >
                    <Sparkles className="h-4 w-4" />
                  </button>
                </div>

                {noteSummary && (
                  <div className="p-4 rounded-xl bg-slate-900 border border-slate-850 text-xs text-slate-400 leading-relaxed italic">
                    {noteSummary}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab Content: Chat */}
        {activeTab === 'chat' && (
          <div className="glass rounded-2xl flex flex-col h-[400px] border border-slate-800/80">
            <div className="flex-1 p-4 overflow-y-auto space-y-3">
              {chatMessages.length > 0 ? (
                chatMessages.map((msg, i) => (
                  <div 
                    key={i} 
                    className={`flex ${msg.sender === 'student' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                      msg.sender === 'student'
                        ? 'bg-brand-600 text-white rounded-tr-none'
                        : 'bg-slate-900 border border-slate-800 text-slate-300 rounded-tl-none'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-500 text-xs py-8">
                  Ask EduTwin about specific topics in this lesson!
                </div>
              )}
            </div>

            <div className="p-3 border-t border-slate-900 flex items-center space-x-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask a question..."
                className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
              />
              <button
                onClick={handleSendMessage}
                disabled={sendingMsg}
                className="p-2.5 rounded-xl bg-brand-600 text-white hover:bg-brand-500 transition cursor-pointer"
              >
                <Send className="h-4.5 w-4.5" />
              </button>
            </div>
          </div>
        )}

        {/* Tab Content: Handouts */}
        {activeTab === 'handouts' && (
          <div className="glass p-5 rounded-2xl space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Lesson handouts</h4>
            {loadingHandouts ? (
              <div className="flex h-20 items-center justify-center">
                <div className="h-5 w-5 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
              </div>
            ) : handouts.length > 0 ? (
              <div className="space-y-3">
                {handouts.map((h) => {
                  const getDownloadUrl = (noteId) => {
                    const base = api.defaults.baseURL || 'https://virtual-ai-tutor-tqet.onrender.com/api/v1';
                    return `${base}/lms-notes/${noteId}/file`;
                  };
                  return (
                    <div key={h.id} className="p-3.5 rounded-xl bg-slate-900 border border-slate-850 space-y-2 text-xs">
                      <div className="flex justify-between items-start gap-1">
                        <span className="font-bold text-slate-200 line-clamp-1">{h.title}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 uppercase shrink-0">
                          {h.file_type}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">{h.description}</p>
                      
                      <div className="flex gap-2 mt-2 pt-2 border-t border-slate-950">
                        {h.file_type.toLowerCase() === 'pdf' && (
                          <button
                            onClick={() => window.open(getDownloadUrl(h.id), '_blank')}
                            className="flex-1 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-800 text-[10px] font-bold text-slate-400 hover:text-slate-300 transition flex items-center justify-center gap-1 cursor-pointer"
                          >
                            <span>Preview</span>
                          </button>
                        )}
                        <a
                          href={getDownloadUrl(h.id)}
                          download
                          onClick={() => setTimeout(() => fetchHandouts(), 1000)}
                          className="flex-1 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-[10px] font-bold text-white transition flex items-center justify-center gap-1 text-center"
                        >
                          <span>Get File</span>
                        </a>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 text-xs">
                No handouts published for this lesson yet.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LessonPage;
