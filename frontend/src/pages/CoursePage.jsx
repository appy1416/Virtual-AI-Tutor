import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { BookOpen, GraduationCap, CheckCircle, Play, ChevronRight, Lock, FileText, Download, Eye } from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const CoursePage = () => {
  const { courseId } = useParams();
  const { data: course, loading: courseLoading, call: fetchCourse } = useApi(() => api.get(`/courses/${courseId}`));
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [loadingEnroll, setLoadingEnroll] = useState(false);

  // Handouts state
  const [handouts, setHandouts] = useState([]);
  const [loadingHandouts, setLoadingHandouts] = useState(false);

  const fetchEnrollments = async () => {
    try {
      const res = await api.get('/courses/enrolled');
      const enrolled = res.data?.data || [];
      setEnrolledCourses(enrolled);
      setIsEnrolled(enrolled.some(c => c.course_id === courseId));
    } catch (e) {
      // Ignored
    }
  };

  const fetchHandouts = async () => {
    setLoadingHandouts(true);
    try {
      const res = await api.get(`/lms-notes?course_id=${courseId}`);
      setHandouts(res.data?.data || []);
    } catch (e) {
      // Ignored
    } finally {
      setLoadingHandouts(false);
    }
  };

  useEffect(() => {
    fetchCourse();
    fetchEnrollments();
    fetchHandouts();
  }, [courseId]);

  const handleEnroll = async () => {
    setLoadingEnroll(true);
    try {
      if (isEnrolled) {
        await api.post(`/courses/${courseId}/unenroll`);
        setIsEnrolled(false);
      } else {
        await api.post(`/courses/${courseId}/enroll`);
        setIsEnrolled(true);
      }
      fetchEnrollments();
    } catch (e) {
      // Ignored
    } finally {
      setLoadingEnroll(false);
    }
  };

  const getDownloadUrl = (noteId) => {
    const base = api.defaults.baseURL || 'https://virtual-ai-tutor-tqet.onrender.com/api/v1';
    return `${base}/lms-notes/${noteId}/file`;
  };

  if (courseLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-12 text-slate-500 text-sm">
        Course not found.
      </div>
    );
  }

  const lessons = course.lessons || [];

  return (
    <div className="space-y-8">
      {/* Course Header Banner */}
      <div className="glass p-8 rounded-3xl relative overflow-hidden border border-brand-500/20">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/10 rounded-full blur-[70px] -mr-24 -mt-24 pointer-events-none" />
        
        <div className="relative flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-4 max-w-2xl">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-bold text-brand-400 px-2 py-1 rounded bg-brand-500/10 border border-brand-500/20">
                {course.category}
              </span>
              <span className="text-[10px] uppercase font-bold text-slate-400 px-2 py-1 rounded bg-slate-900 border border-slate-800 capitalize">
                {course.level}
              </span>
            </div>
            
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-100 leading-tight">{course.title}</h1>
            <p className="text-slate-400 text-sm leading-relaxed">{course.description}</p>
          </div>

          <button
            onClick={handleEnroll}
            disabled={loadingEnroll}
            className={`px-8 py-3.5 rounded-full font-bold text-sm select-none active:scale-[0.98] transition cursor-pointer shrink-0 ${
              isEnrolled
                ? 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-300'
                : 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/20'
            }`}
          >
            {loadingEnroll ? 'Loading...' : isEnrolled ? 'Enrolled' : 'Enroll Now'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Syllabus / Lessons (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
              <BookOpen className="h-5 w-5 text-brand-400" />
              <span>Course Syllabus ({lessons.length} Lessons)</span>
            </h2>
          </div>

          <div className="space-y-4">
            {lessons.length > 0 ? (
              lessons.map((lesson, index) => (
                <div 
                  key={lesson.id}
                  className="glass p-5 rounded-2xl flex items-center justify-between hover:border-brand-500/20 transition duration-200"
                >
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center font-bold text-brand-400">
                      {index + 1}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-200">{lesson.title}</h3>
                      <p className="text-xs text-slate-400 line-clamp-1">{lesson.description}</p>
                    </div>
                  </div>

                  {isEnrolled ? (
                    <Link 
                      to={`/lessons/${lesson.id}`}
                      className="p-2.5 rounded-full bg-brand-600/10 border border-brand-500/20 text-brand-400 hover:bg-brand-600 hover:text-white transition duration-200"
                    >
                      <Play className="h-4 w-4 fill-current ml-0.5" />
                    </Link>
                  ) : (
                    <div className="p-2.5 rounded-full bg-slate-900 border border-slate-800 text-slate-600" title="Enroll to unlock">
                      <Lock className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-500 text-sm">
                No lessons published for this course yet.
              </div>
            )}
          </div>
        </div>

        {/* Handouts Sidebar Panel (1 Col) */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
              <FileText className="h-5 w-5 text-brand-400" />
              <span>Study Handouts</span>
            </h2>
          </div>

          <div className="glass p-6 rounded-2xl border border-slate-800 space-y-4">
            {loadingHandouts ? (
              <div className="flex h-20 items-center justify-center">
                <div className="h-5 w-5 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
              </div>
            ) : handouts.length > 0 ? (
              <div className="space-y-3.5">
                {handouts.map((h) => (
                  <div key={h.id} className="p-3.5 rounded-xl bg-slate-900 border border-slate-850 space-y-2 text-xs">
                    <div className="flex justify-between items-start gap-1">
                      <span className="font-bold text-slate-200 line-clamp-1">{h.title}</span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 uppercase shrink-0">
                        {h.file_type}
                      </span>
                    </div>
                    <p className="text-slate-400 line-clamp-1 text-[11px]">{h.description}</p>
                    
                    {isEnrolled ? (
                      <div className="flex gap-2 mt-2 pt-2 border-t border-slate-950">
                        {h.file_type.toLowerCase() === 'pdf' && (
                          <button
                            onClick={() => window.open(getDownloadUrl(h.id), '_blank')}
                            className="flex-1 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-800 text-[10px] font-bold text-slate-400 hover:text-slate-300 transition flex items-center justify-center gap-1 cursor-pointer"
                          >
                            <Eye className="h-3 w-3" />
                            <span>Preview</span>
                          </button>
                        )}
                        <a
                          href={getDownloadUrl(h.id)}
                          download
                          onClick={() => setTimeout(() => fetchHandouts(), 1000)}
                          className="flex-1 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-[10px] font-bold text-white transition flex items-center justify-center gap-1 text-center"
                        >
                          <Download className="h-3 w-3" />
                          <span>Get File</span>
                        </a>
                      </div>
                    ) : (
                      <div className="text-[10px] text-slate-600 italic mt-2 text-center">
                        Enroll to unlock download
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 text-xs">
                No handouts published for this course yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoursePage;
