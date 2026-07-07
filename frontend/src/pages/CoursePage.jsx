import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { BookOpen, GraduationCap, CheckCircle, Play, ChevronRight, Lock } from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const CoursePage = () => {
  const { courseId } = useParams();
  const { data: course, loading: courseLoading, call: fetchCourse } = useApi(() => api.get(`/courses/${courseId}`));
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [loadingEnroll, setLoadingEnroll] = useState(false);

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

  useEffect(() => {
    fetchCourse();
    fetchEnrollments();
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

      {/* Syllabus / Lessons */}
      <div className="space-y-6">
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
    </div>
  );
};

export default CoursePage;
