import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, GraduationCap, PlusCircle, BookOpen } from 'lucide-react';
import api from '../config/api';
import { useApi } from '../hooks/useApi';

const CourseList = () => {
  const { data: courses, loading, error, call: fetchCourses } = useApi(() => api.get('/courses'));
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    fetchCourses();
  }, []);

  const items = courses?.items || [];

  // Filter logic
  const filteredCourses = items.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          course.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || course.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = ['All', ...new Set(items.map(c => c.category))];

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Browse Course Catalog</h1>
          <p className="text-slate-400 text-sm mt-1">Explore structured learning paths tailored to your needs</p>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search courses..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
          />
        </div>

        {/* Categories Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-4 py-2 rounded-xl text-xs font-bold border transition cursor-pointer shrink-0 ${
                selectedCategory === cat
                  ? 'bg-brand-600 border-brand-500 text-white'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Courses Grid */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-400 text-sm bg-red-500/5 rounded-2xl border border-red-500/10">
          Failed to fetch courses: {error}
        </div>
      ) : filteredCourses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((course) => (
            <Link 
              key={course.id} 
              to={`/courses/${course.id}`}
              className="glass p-6 rounded-2xl flex flex-col justify-between hover:border-brand-500/30 transition duration-300 group"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-brand-400 px-2 py-1 rounded bg-brand-500/10 border border-brand-500/20">
                    {course.category}
                  </span>
                  <span className="text-[10px] uppercase font-bold text-slate-400 px-2 py-1 rounded bg-slate-900 border border-slate-800 capitalize">
                    {course.level}
                  </span>
                </div>

                <div className="space-y-2">
                  <h3 className="text-lg font-bold group-hover:text-brand-300 transition leading-snug">
                    {course.title}
                  </h3>
                  <p className="text-xs text-slate-400 leading-normal line-clamp-3">
                    {course.description}
                  </p>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-900/80 mt-6 flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center space-x-1.5 font-medium">
                  <GraduationCap className="h-4.5 w-4.5" />
                  <span>By Tutor</span>
                </span>
                <span className="text-brand-400 font-bold group-hover:translate-x-1 transition-transform flex items-center space-x-0.5">
                  <span>View Details</span>
                  <BookOpen className="h-3.5 w-3.5 ml-0.5" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500 text-sm">
          No courses match your filter or search term.
        </div>
      )}
    </div>
  );
};

export default CourseList;
