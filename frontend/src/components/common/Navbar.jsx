import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { LogOut, User, Menu } from 'lucide-react';
import { AuthContext } from '../../context/AuthContext';

const Navbar = ({ onToggleSidebar }) => {
  const { user, logout } = useContext(AuthContext);

  return (
    <nav className="glass fixed top-0 left-0 right-0 z-40 h-16 px-4 md:px-6 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <button 
          onClick={onToggleSidebar} 
          className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-900 transition md:hidden"
        >
          <Menu className="h-6 w-6" />
        </button>
        <Link to="/" className="text-xl font-extrabold bg-gradient-to-r from-brand-400 to-indigo-400 bg-clip-text text-transparent tracking-tight">
          EduTwin AI
        </Link>
      </div>

      {user && (
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex flex-col text-right">
            <span className="text-sm font-semibold text-slate-100">{user.full_name}</span>
            <span className="text-xs text-slate-400 capitalize">{user.role}</span>
          </div>
          <Link to="/profile" className="p-2 text-slate-400 hover:text-white rounded-full bg-slate-900 border border-slate-800 transition">
            <User className="h-4.5 w-4.5" />
          </Link>
          <button 
            onClick={logout}
            className="p-2 text-red-400 hover:text-red-300 rounded-full hover:bg-slate-900 transition cursor-pointer"
            title="Log Out"
          >
            <LogOut className="h-4.5 w-4.5" />
          </button>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
