import React, { useEffect, useState, useRef } from 'react';
import { 
  Send, 
  Mic, 
  MicOff, 
  Plus, 
  MessageSquare, 
  Upload, 
  AlertCircle,
  Play,
  Volume2
} from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const ChatPage = () => {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sending, setSending] = useState(false);

  // Audio Recorder State
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const audioChunks = useRef([]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await api.get('/chat/search?q=');
      const list = res.data?.data || [];
      setSessions(list);
      if (list.length > 0 && !activeSessionId) {
        handleSelectSession(list[0].id);
      }
    } catch (e) {
      // Ignored
    }
  };

  const handleSelectSession = async (sessionId) => {
    setActiveSessionId(sessionId);
    try {
      const res = await api.get(`/chat/${sessionId}/messages`);
      setMessages(res.data?.data || []);
    } catch (e) {
      // Ignored
    }
  };

  const handleCreateSession = async () => {
    try {
      const res = await api.post('/chat/start', { lesson_id: null, course_id: null });
      const newSess = res.data.data;
      setSessions(prev => [newSess, ...prev]);
      setActiveSessionId(newSess.id);
      setMessages([]);
    } catch (e) {
      // Ignored
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !activeSessionId) return;
    const userMsg = chatInput;
    setChatInput('');
    setMessages(prev => [...prev, { sender: 'student', content: userMsg, timestamp: new Date().toISOString() }]);
    setSending(true);
    try {
      const res = await api.post(`/chat/${activeSessionId}/message`, { message: userMsg });
      const { user_message, ai_response } = res.data.data;
      setMessages(prev => [
        ...prev.filter(m => m.content !== userMsg),
        user_message,
        ai_response
      ]);
    } catch (e) {
      // Ignored
    } finally {
      setSending(false);
    }
  };

  // Audio Recorder Routines
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunks.current = [];
      
      recorder.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunks.current, { type: 'audio/mp3' });
        setAudioBlob(blob);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
    } catch (e) {
      alert('Microphone access denied or unsupported by browser.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && recording) {
      mediaRecorder.stop();
      setRecording(false);
    }
  };

  const handleUploadAudio = async () => {
    if (!audioBlob || !activeSessionId) return;
    setSending(true);
    const formData = new FormData();
    formData.append('file', audioBlob, 'voice_input.mp3');
    try {
      // Create voice log session, upload audio, transcribe, get reply
      const voiceRes = await api.post('/voice/sessions', { tutor_type: 'ai_voice', lesson_id: null });
      const voiceSessionId = voiceRes.data.data.id;
      
      const uploadRes = await api.post(`/voice/sessions/${voiceSessionId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const transcript = uploadRes.data.data.transcription;

      // Inject transcription into current chat session
      setMessages(prev => [...prev, { sender: 'student', content: transcript, timestamp: new Date().toISOString() }]);
      const res = await api.post(`/chat/${activeSessionId}/message`, { message: transcript });
      const { user_message, ai_response } = res.data.data;
      
      setMessages(prev => [
        ...prev.filter(m => m.content !== transcript),
        user_message,
        ai_response
      ]);
      setAudioBlob(null);
    } catch (e) {
      alert('Failed to upload audio. Size might be too large or format unsupported.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">AI Dialogue Companion</h1>
          <p className="text-slate-400 text-sm mt-1">Converse with EduTwin using text or recorded speech clips</p>
        </div>
        <button
          onClick={handleCreateSession}
          className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 font-bold text-xs text-white flex items-center space-x-1.5 shadow-lg shadow-brand-500/20 active:scale-95 transition cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Sessions Sidebar Column */}
        <div className="md:col-span-1 glass p-4 rounded-2xl flex flex-col space-y-3 h-[500px] overflow-y-auto pr-1">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider px-2">Active Conversations</span>
          {sessions.length > 0 ? (
            sessions.map((sess) => (
              <button
                key={sess.id}
                onClick={() => handleSelectSession(sess.id)}
                className={`w-full p-3 rounded-xl border text-left flex items-center space-x-3 transition cursor-pointer ${
                  activeSessionId === sess.id
                    ? 'bg-brand-600/10 border-brand-500 text-brand-300'
                    : 'bg-slate-900 border-slate-850 hover:border-slate-800 text-slate-400'
                }`}
              >
                <MessageSquare className="h-4.5 w-4.5 shrink-0" />
                <span className="text-xs truncate font-medium">Session ID: {sess.id.slice(0, 8)}</span>
              </button>
            ))
          ) : (
            <div className="text-center py-12 text-slate-600 text-xs">
              No conversations. Create one!
            </div>
          )}
        </div>

        {/* Chat Stream Column */}
        <div className="md:col-span-3 glass rounded-2xl flex flex-col h-[500px] border border-slate-800">
          {activeSessionId ? (
            <>
              {/* Messages list */}
              <div className="flex-1 p-6 overflow-y-auto space-y-4">
                {messages.length > 0 ? (
                  messages.map((msg, i) => (
                    <div 
                      key={i}
                      className={`flex ${(msg.sender === 'student' || msg.role === 'user') ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[75%] rounded-2xl p-4 text-xs leading-relaxed ${
                        (msg.sender === 'student' || msg.role === 'user')
                          ? 'bg-brand-600 text-white rounded-tr-none shadow-lg shadow-brand-500/10'
                          : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-slate-500 text-xs py-12">
                    Start of conversation. Type below or hold to speak!
                  </div>
                )}
              </div>

              {/* Audio feedback actions */}
              {audioBlob && (
                <div className="px-4 py-2 border-t border-slate-900/60 bg-brand-500/5 flex items-center justify-between text-xs text-brand-300">
                  <span className="flex items-center space-x-1.5">
                    <Volume2 className="h-4 w-4" />
                    <span>Voice clip ready ({Math.round(audioBlob.size / 1024)} KB)</span>
                  </span>
                  <div className="flex items-center space-x-2">
                    <button onClick={() => setAudioBlob(null)} className="text-red-400 font-bold hover:underline cursor-pointer">Discard</button>
                    <button onClick={handleUploadAudio} className="px-3 py-1 rounded-lg bg-brand-600 text-white font-bold cursor-pointer">Upload Speech</button>
                  </div>
                </div>
              )}

              {/* Inputs row */}
              <div className="p-4 border-t border-slate-900 flex items-center space-x-3">
                <button
                  onClick={recording ? stopRecording : startRecording}
                  className={`p-3 rounded-xl border transition cursor-pointer ${
                    recording
                      ? 'bg-red-500/10 border-red-500 text-red-400 animate-pulse'
                      : 'bg-slate-900 border-slate-850 text-slate-400 hover:text-slate-200'
                  }`}
                  title={recording ? 'Stop Recording' : 'Record Speech'}
                >
                  {recording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                </button>

                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask a question..."
                  className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
                />

                <button
                  onClick={handleSendMessage}
                  disabled={sending || !chatInput.trim()}
                  className="p-3.5 rounded-xl bg-brand-600 text-white hover:bg-brand-500 transition disabled:opacity-50 cursor-pointer"
                >
                  <Send className="h-4.5 w-4.5" />
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <MessageSquare className="h-12 w-12 text-slate-700 mb-4" />
              <h3 className="text-sm font-bold text-slate-400">No Session Selected</h3>
              <p className="text-xs text-slate-500 mt-1">Select a conversation or click "New Chat" to begin</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
