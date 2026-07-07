import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { HelpCircle, Clock, Award, ShieldAlert, AlertCircle, RefreshCw, CheckCircle, Zap } from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const QuizPage = () => {
  const { quizId } = useParams();
  const { data: quiz, loading: quizLoading, error: quizError, call: fetchQuiz } = useApi(() => api.get(`/quizzes/${quizId}`));
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [attemptError, setAttemptError] = useState('');
  
  // Timer countdown state
  const [timeLeft, setTimeLeft] = useState(null);

  useEffect(() => {
    fetchQuiz();
  }, [quizId]);

  useEffect(() => {
    if (quiz && quiz.time_limit_seconds) {
      setTimeLeft(quiz.time_limit_seconds);
    }
  }, [quiz]);

  useEffect(() => {
    if (timeLeft === null || result) return;
    if (timeLeft === 0) {
      handleSubmit();
      return;
    }
    const t = setTimeout(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);
    return () => clearTimeout(t);
  }, [timeLeft, result]);

  const handleSubmit = async () => {
    const answer = selectedAnswer || 'No answer submitted (Timed out)';
    setSubmitting(true);
    setAttemptError('');
    try {
      const res = await api.post(`/quizzes/${quizId}/submit`, {
        user_answer: answer,
        time_spent_seconds: quiz?.time_limit_seconds ? (quiz.time_limit_seconds - (timeLeft || 0)) : 30
      });
      setResult(res.data.data);
    } catch (e) {
      setAttemptError(e.response?.data?.message || e.message || 'Failed to submit quiz attempt.');
    } finally {
      setSubmitting(false);
    }
  };

  if (quizLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
      </div>
    );
  }

  if (quizError || !quiz) {
    return (
      <div className="text-center py-12 text-slate-500 text-sm">
        Quiz details could not be loaded or retrieved.
      </div>
    );
  }

  const options = quiz.options || [];

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Quiz Card */}
      <div className="glass p-8 rounded-3xl space-y-6 relative overflow-hidden border border-brand-500/10">
        <div className="absolute top-0 right-0 w-60 h-60 bg-indigo-500/5 rounded-full blur-[50px] -mr-10 -mt-10 pointer-events-none" />
        
        <div className="flex items-center justify-between border-b border-slate-900 pb-4 relative z-10">
          <div className="flex items-center space-x-2 text-brand-400">
            <HelpCircle className="h-5 w-5" />
            <span className="text-sm font-bold uppercase tracking-wider">Concept Verification</span>
          </div>
          <div className="flex items-center space-x-4 text-xs text-slate-500">
            {timeLeft !== null && (
              <span className="flex items-center space-x-1 font-mono text-orange-400 font-bold bg-orange-400/10 border border-orange-400/20 px-2.5 py-1 rounded-lg">
                <Clock className="h-3.5 w-3.5" />
                <span>Timer: {timeLeft}s</span>
              </span>
            )}
            <span className="flex items-center space-x-1">
              <Award className="h-4 w-4" />
              <span>Passing: {quiz.passing_score || 70}%</span>
            </span>
          </div>
        </div>

        {attemptError && (
          <div className="flex items-center space-x-2 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <ShieldAlert className="h-5 w-5 shrink-0" />
            <span>{attemptError}</span>
          </div>
        )}

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-100 leading-snug">{quiz.question_text}</h2>
        </div>

        {/* Answers / Options */}
        <div className="space-y-3 relative z-10">
          {quiz.quiz_type === 'mcq' && options.length > 0 ? (
            options.map((opt, i) => (
              <label 
                key={i}
                className={`flex items-center space-x-3 p-4 rounded-xl border transition cursor-pointer select-none ${
                  selectedAnswer === opt.option_text
                    ? 'bg-brand-600/20 border-brand-500 text-brand-300'
                    : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                } ${result ? 'pointer-events-none opacity-60' : ''}`}
              >
                <input
                  type="radio"
                  name="quiz-option"
                  value={opt.option_text}
                  checked={selectedAnswer === opt.option_text}
                  onChange={(e) => setSelectedAnswer(e.target.value)}
                  disabled={result}
                  className="accent-brand-500 h-4.5 w-4.5 cursor-pointer"
                />
                <span className="text-sm">{opt.option_text}</span>
              </label>
            ))
          ) : quiz.quiz_type === 'essay' ? (
            <textarea
              value={selectedAnswer}
              onChange={(e) => setSelectedAnswer(e.target.value)}
              disabled={result}
              placeholder="Write down your essay response here..."
              className="w-full h-48 p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition resize-none"
            />
          ) : (
            <input
              type="text"
              value={selectedAnswer}
              onChange={(e) => setSelectedAnswer(e.target.value)}
              disabled={result}
              placeholder="Type your short answer..."
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
            />
          )}
        </div>

        {!result ? (
          <button
            onClick={handleSubmit}
            disabled={submitting || !selectedAnswer.trim()}
            className="w-full py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 active:scale-[0.98] font-bold text-white shadow-lg shadow-brand-500/20 flex items-center justify-center space-x-2 transition disabled:opacity-50 cursor-pointer"
          >
            {submitting ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <span>Submit Answer</span>
            )}
          </button>
        ) : (
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 relative z-10 animate-fade-in">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-bold flex items-center gap-1.5">
                <CheckCircle className={`h-4.5 w-4.5 ${result.is_correct ? 'text-emerald-400' : 'text-red-400'}`} />
                <span>Result Evaluation</span>
              </span>
              <span className={`text-xs font-extrabold px-3 py-1 rounded-full ${
                result.is_correct
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-red-500/10 text-red-400 border border-red-500/20'
              }`}>
                {result.score}% Score
              </span>
            </div>
            
            <p className="text-sm text-slate-300 leading-relaxed italic">
              "{result.feedback}"
            </p>

            {/* Rewards Alert */}
            {result.points_awarded > 0 && (
              <div className="p-3.5 bg-emerald-500/5 border border-emerald-500/20 rounded-xl flex items-center justify-between">
                <span className="text-xs text-slate-400">XP Points Awarded</span>
                <span className="text-xs text-emerald-400 font-extrabold flex items-center gap-1">
                  <Zap className="h-4 w-4 fill-current" />
                  <span>+{result.points_awarded} XP</span>
                </span>
              </div>
            )}

            {/* Explanation & Correct answer */}
            {!result.is_correct && result.correct_answer && (
              <div className="text-xs p-3 rounded-lg bg-slate-950 border border-slate-900 text-slate-400">
                <strong className="text-red-400 block mb-1">Correct Answer:</strong>
                <span className="font-mono">{result.correct_answer}</span>
              </div>
            )}

            {result.explanation && (
              <div className="text-xs p-3.5 rounded-xl bg-brand-500/5 border border-brand-500/20 text-slate-300 leading-relaxed">
                <strong className="text-brand-400 block mb-1">Tutor Explanation:</strong>
                {result.explanation}
              </div>
            )}
            
            <div className="pt-2 flex gap-4">
              <Link 
                to={`/lessons/${quiz.lesson_id}`} 
                className="flex-1 py-3 text-center text-xs font-bold rounded-xl bg-slate-950 border border-slate-850 hover:bg-slate-900 text-slate-400 hover:text-white transition"
              >
                Return to Lesson
              </Link>
              <button 
                onClick={() => {
                  setResult(null);
                  setSelectedAnswer('');
                  if (quiz.time_limit_seconds) {
                    setTimeLeft(quiz.time_limit_seconds);
                  }
                }}
                className="flex-1 py-3 text-center text-xs font-bold rounded-xl bg-brand-600 hover:bg-brand-500 text-white transition cursor-pointer"
              >
                Retry Quiz
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuizPage;
