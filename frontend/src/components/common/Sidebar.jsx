import React, { useContext } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BookOpen, 
  StickyNote, 
  MessageSquare, 
  BarChart3, 
  User, 
  Settings, 
  Shield, 
  Users 
} from 'lucide-react';
import { AuthContext } from '../../context/AuthContext';

const Sidebar = ({ isOpen, onClose }) => {
  const { user } = useContext(AuthContext);

  if (!user) return null;

  const studentLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/courses', label: 'Courses', icon: BookOpen },
    { to: '/notes', label: 'Notes', icon: StickyNote },
    { to: '/chat', label: 'AI Chat', icon: MessageSquare },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/profile', label: 'Learning Twin', icon: User },
  ];

  const adminLinks = [
    { to: '/admin', label: 'Admin Dashboard', icon: Shield },
    { to: '/admin/users', label: 'User Management', icon: Users },
  ];

  const activeStyle = "flex items-center space-x-3 px-4 py-3 rounded-xl bg-brand-600/30 text-brand-300 border border-brand-500/20 font-medium transition duration-200";
  const inactiveStyle = "flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-900/50 hover:border-slate-800 border border-transparent transition duration-200";

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          onClick={onClose}
          className="fixed inset-0 z-30 bg-slate-950/80 backdrop-blur-sm md:hidden"
        />
      )}

      <aside className={`glass fixed top-16 bottom-0 left-0 z-30 w-64 p-4 transform transition-transform duration-300 ease-in-out md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col h-full justify-between">
          <div className="space-y-1">
            {user.role === 'student' && studentLinks.map((link) => (
              <NavLink 
                key={link.to} 
                to={link.to} 
                onClick={onClose}
                className={({ isActive }) => isActive ? activeStyle : inactiveStyle}
              >
                <link.icon className="h-5 w-5" />
                <span>{link.label}</span>
              </NavLink>
            ))}

            {user.role === 'admin' && adminLinks.map((link) => (
              <NavLink 
                key={link.to} 
                to={link.to} 
                onClick={onClose}
                className={({ isActive }) => isActive ? activeStyle : inactiveStyle}
              >
                <link.icon className="h-5 w-5" />
                <span>{link.label}</span>
              </NavLink>
            ))}
          </div>

          <div className="border-t border-slate-800/80 pt-4 pb-2 text-center text-xs text-slate-500">
            &copy; {new Date().getFullYear()} EduTwin AI
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
