import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, BrainCircuit, Sparkles, MessageSquare, Mic, ArrowRight } from 'lucide-react';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between overflow-x-hidden selection:bg-brand-500 selection:text-white">
      {/* Top Navbar */}
      <header className="max-w-7xl mx-auto px-6 h-20 w-full flex items-center justify-between z-10">
        <span className="text-2xl font-extrabold bg-gradient-to-r from-brand-400 to-indigo-400 bg-clip-text text-transparent tracking-tight">
          EduTwin AI
        </span>
        <div className="flex items-center space-x-4">
          <Link to="/login" className="text-sm font-semibold hover:text-brand-300 transition">
            Sign In
          </Link>
          <Link to="/register" className="px-4 py-2 text-sm font-semibold rounded-full bg-brand-600 hover:bg-brand-500 shadow-lg shadow-brand-500/20 active:scale-95 transition">
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-12 md:py-20 flex-1 flex flex-col items-center text-center justify-center relative">
        {/* Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] md:w-[600px] h-[350px] md:h-[600px] bg-brand-500/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="relative space-y-6 max-w-4xl">
          <span className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-brand-500/30 text-xs font-semibold text-brand-300">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Introducing Next-Gen Personalized Tutoring</span>
          </span>

          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight leading-none">
            Meet Your <span className="bg-gradient-to-r from-brand-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">AI Learning Twin</span>
          </h1>

          <p className="text-base sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            EduTwin adapts to your learning pace, analyzes your knowledge gaps dynamically, drafts study logs, and hosts voice interactions to ensure concept mastery.
          </p>

          <div className="pt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register" className="w-full sm:w-auto px-8 py-4 rounded-full bg-gradient-to-r from-brand-600 to-indigo-600 font-bold hover:opacity-90 shadow-xl shadow-brand-500/20 flex items-center justify-center space-x-2 group active:scale-95 transition cursor-pointer">
              <span>Start Learning Free</span>
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link to="/login" className="w-full sm:w-auto px-8 py-4 rounded-full bg-slate-900 border border-slate-800 font-bold hover:bg-slate-800 flex items-center justify-center transition">
              <span>Sign In to Account</span>
            </Link>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <section className="mt-24 w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
          <div className="glass p-6 rounded-2xl flex flex-col items-start space-y-4 hover:border-brand-500/30 transition">
            <div className="p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
              <BrainCircuit className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold">Dynamic Twin Mappings</h3>
            <p className="text-sm text-slate-400 leading-relaxed text-left">
              BKT models track your knowledge gaps dynamically and generate custom schedules.
            </p>
          </div>

          <div className="glass p-6 rounded-2xl flex flex-col items-start space-y-4 hover:border-brand-500/30 transition">
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <MessageSquare className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold">Adaptive AI Tutor Chat</h3>
            <p className="text-sm text-slate-400 leading-relaxed text-left">
              Speak or type to a real-time chatbot that adapts questions to your profile.
            </p>
          </div>

          <div className="glass p-6 rounded-2xl flex flex-col items-start space-y-4 hover:border-brand-500/30 transition">
            <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
              <BookOpen className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold">Concept Recommendations</h3>
            <p className="text-sm text-slate-400 leading-relaxed text-left">
              Heuristic engines match target content to clear your low scoring weaknesses.
            </p>
          </div>

          <div className="glass p-6 rounded-2xl flex flex-col items-start space-y-4 hover:border-brand-500/30 transition">
            <div className="p-3 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-400">
              <Mic className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold">Audio Dialogues</h3>
            <p className="text-sm text-slate-400 leading-relaxed text-left">
              Upload speech clips and receive synthesized voice responses directly.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-8 text-center text-xs text-slate-500">
        &copy; {new Date().getFullYear()} EduTwin AI. All rights reserved.
      </footer>
    </div>
  );
};

export default LandingPage;
