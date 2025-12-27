import React, { useState, useRef, useEffect } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { User, LogOut, ChevronDown } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const Layout: React.FC = () => {
  const location = useLocation();
  const { session, user, signOut, loading, isAdmin } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const handleSignOut = async () => {
    await signOut();
    setDropdownOpen(false);
  };

  const navLinkClass = (path: string) =>
    `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive(path)
        ? "bg-primary-700 text-white"
        : "text-primary-100 hover:bg-primary-700/50 hover:text-white"
    }`;

  return (
    <div className="min-h-screen flex flex-col bg-neutral-cloud">
      {/* Navigation Bar - 80px height, Deep Slate background */}
      <header className="bg-primary-800 text-white shadow-soft-lg">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex justify-between items-center" style={{ height: '80px' }}>
            {/* Logo & Branding */}
            <Link to="/" className="flex items-center space-x-2">
              <span className="text-xl font-semibold">AI WebScraper</span>
              <span className="text-secondary-500 text-sm">| by CushLabs.ai</span>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center space-x-1">
              <Link to="/dashboard" className={navLinkClass("/dashboard")}>
                Dashboard
              </Link>
              <Link to="/crawls" className={navLinkClass("/crawls")}>
                Crawls
              </Link>
              {isAdmin && (
                <Link to="/users" className={navLinkClass("/users")}>
                  Users
                </Link>
              )}
              <Link to="/docs" className={navLinkClass("/docs")}>
                Docs
              </Link>
            </nav>

            {/* User Menu */}
            <div className="flex items-center">
              {loading ? (
                <div className="text-primary-200 text-sm">Loading...</div>
              ) : session && user ? (
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium text-primary-100 hover:bg-primary-700/50 hover:text-white transition-colors"
                  >
                    <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                    <span className="hidden sm:inline">{user.email}</span>
                    <ChevronDown
                      className={`w-4 h-4 transition-transform ${
                        dropdownOpen ? "rotate-180" : ""
                      }`}
                    />
                  </button>

                  {/* Dropdown Menu */}
                  {dropdownOpen && (
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-soft-lg border border-primary-100 py-1 z-50">
                      <div className="px-4 py-3 border-b border-primary-50">
                        <p className="text-sm font-semibold text-neutral-charcoal truncate">
                          {user.email}
                        </p>
                        <p className="text-xs text-neutral-steel mt-0.5">
                          {isAdmin ? "Admin" : "User"}
                        </p>
                      </div>

                      <Link
                        to="/profile"
                        className="flex items-center gap-2 px-4 py-2.5 text-sm text-neutral-charcoal hover:bg-primary-50 transition-colors"
                        onClick={() => setDropdownOpen(false)}
                      >
                        <User className="w-4 h-4" />
                        Profile Settings
                      </Link>

                      <button
                        onClick={handleSignOut}
                        className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-error-600 hover:bg-error-50 transition-colors border-t border-primary-50"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Pale Cloud background */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-primary-100">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-sm text-neutral-steel">
              &copy; {new Date().getFullYear()} AI WebScraper by CushLabs.ai. All rights reserved.
            </div>
            <div className="flex space-x-6">
              <Link
                to="/privacy"
                className="text-sm text-neutral-steel hover:text-neutral-charcoal transition-colors"
              >
                Privacy Policy
              </Link>
              <Link
                to="/terms"
                className="text-sm text-neutral-steel hover:text-neutral-charcoal transition-colors"
              >
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