import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Layout: React.FC = () => {
  const location = useLocation();
  const { session, user, signOut, loading } = useAuth();
  
  const isActive = (path: string) => {
    return location.pathname === path ? 'bg-primary-700 text-white' : 'text-primary-100 hover:bg-primary-600 hover:text-white';
  };

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-primary-800 text-white shadow-md">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold">AAA WebScraper</Link>
          <nav className="hidden md:flex space-x-4">
            <Link to="/dashboard" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/dashboard')}`}>
              Dashboard
            </Link>
            <Link to="/crawls" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/crawls')}`}>
              Crawls
            </Link>
            <Link to="/users" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/users')}`}>
              Users
            </Link>
            <Link to="/profile" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/profile')}`}>
              Profile
            </Link>
            <Link to="/docs" className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/docs')}`}>
              Docs
            </Link>
          </nav>
          
          {/* Authentication Status */}
          <div className="flex items-center space-x-4">
            {loading ? (
              <div className="text-primary-200 text-sm">Loading...</div>
            ) : session && user ? (
              <div className="flex items-center space-x-3">
                <div className="text-primary-200 text-sm">
                  <span className="inline-flex items-center">
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                    {user.email}
                  </span>
                </div>
                <button
                  onClick={handleSignOut}
                  className="text-primary-200 hover:text-white text-sm px-3 py-1 rounded border border-primary-600 hover:border-primary-400 transition-colors"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <div className="text-primary-300 text-sm">
                  <span className="inline-flex items-center">
                    <span className="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                    Not signed in
                  </span>
                </div>
                <Link
                  to="/login"
                  className="text-primary-200 hover:text-white text-sm px-3 py-1 rounded border border-primary-600 hover:border-primary-400 transition-colors"
                >
                  Sign In
                </Link>
              </div>
            )}
          </div>
          
          <div className="md:hidden">
            {/* Mobile menu button would go here */}
            <button className="text-white">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main className="flex-grow container mx-auto px-4 py-8">
        <Outlet />
      </main>

      <footer className="bg-secondary-800 text-white py-6">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <p className="text-sm">&copy; {new Date().getFullYear()} AAA WebScraper. All rights reserved.</p>
            </div>
            <div className="flex space-x-4">
              <Link to="/privacy" className="text-secondary-300 hover:text-white">
                Privacy Policy
              </Link>
              <Link to="/terms" className="text-secondary-300 hover:text-white">
                Terms of Service
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
