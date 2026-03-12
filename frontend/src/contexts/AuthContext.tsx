import React, { createContext, useContext, useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';

interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{
    error: Error | null;
    data: Session | null;
  }>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
  isAdmin: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Get initial session and validate it
    supabase.auth.getSession().then(async ({ data: { session }, error }) => {
      if (error || !session) {
        // Clear invalid session
        await supabase.auth.signOut();
        setSession(null);
        setUser(null);
        setLoading(false);
        return;
      }

      // Validate session is not expired
      const expiresAt = session.expires_at;
      const now = Math.floor(Date.now() / 1000);
      
      if (expiresAt && expiresAt < now) {
        // Session expired, try to refresh
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
        
        if (refreshError || !refreshData.session) {
          // Refresh failed, clear session
          await supabase.auth.signOut();
          setSession(null);
          setUser(null);
          setLoading(false);
          return;
        }
        
        // Use refreshed session
        setSession(refreshData.session);
        setUser(refreshData.session.user);
        checkUserRole(refreshData.session.user.id);
      } else {
        // Session is valid
        setSession(session);
        setUser(session.user);
        checkUserRole(session.user.id);
      }
      
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        if (session?.user) {
          checkUserRole(session.user.id);
        } else {
          setIsAdmin(false);
        }
        setLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Auto-refresh session before it expires (~5 minutes before expiry)
  const refreshTimerRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }

    if (session?.expires_at) {
      const expiresAtMs = session.expires_at * 1000;
      const refreshAtMs = expiresAtMs - (5 * 60 * 1000); // 5 min before expiry
      const delay = refreshAtMs - Date.now();

      if (delay > 0) {
        refreshTimerRef.current = setTimeout(async () => {
          try {
            const { data } = await supabase.auth.refreshSession();
            if (data.session) {
              setSession(data.session);
              setUser(data.session.user);
            }
            // If refresh fails, don't force logout — let the next API call handle it
          } catch (err) {
            console.error('Background session refresh failed:', err);
          }
        }, delay);
      }
    }

    return () => {
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    };
  }, [session?.expires_at]);

  // Check if user is admin
  const checkUserRole = async (userId: string) => {
    try {
      // Use backend API instead of direct Supabase query to avoid RLS issues
      const session = await supabase.auth.getSession();
      const token = session.data.session?.access_token;
      
      const response = await fetch(`${process.env.REACT_APP_API_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        
        // Don't fail silently - this is causing the redirect loop
        // Just set admin to false and continue
        setIsAdmin(false);
        return;
      }
      
      const data = await response.json();
      setIsAdmin(data?.is_admin || false);
    } catch (error) {
      console.error('Error checking user role');
      setIsAdmin(false);
    }
  };

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('Supabase auth error:', error);
        return { data: null, error };
      }

      if (data.session && data.user) {
        await checkUserRole(data.user.id);
      }

      return { data: data.session, error: null };
    } catch (error) {
      console.error('Error signing in:', error);
      return { data: null, error: error as Error };
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      await supabase.auth.signOut();

      setSession(null);
      setUser(null);
      setIsAdmin(false);
    } catch (error) {
      console.error('Error signing out');
    }
  }, []);

  const refreshSession = useCallback(async () => {
    try {
      const { data } = await supabase.auth.refreshSession();
      setSession(data.session);
      setUser(data.session?.user ?? null);
      if (data.session?.user) {
        await checkUserRole(data.session.user.id);
      }
    } catch (error) {
      console.error('Error refreshing session:', error);
    }
  }, []);

  const value = useMemo(() => ({
    session,
    user,
    loading,
    signIn,
    signOut,
    refreshSession,
    isAdmin,
  }), [session, user, loading, signIn, signOut, refreshSession, isAdmin]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
