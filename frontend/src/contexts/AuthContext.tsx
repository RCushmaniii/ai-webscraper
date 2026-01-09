import React, { createContext, useContext, useState, useEffect } from 'react';
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

  // Check if user is admin
  const checkUserRole = async (userId: string) => {
    try {
      console.log('🔍 checkUserRole: Starting for userId:', userId);
      
      // Use backend API instead of direct Supabase query to avoid RLS issues
      const session = await supabase.auth.getSession();
      const token = session.data.session?.access_token;
      
      console.log('🔍 checkUserRole: Token exists:', !!token);
      console.log('🔍 checkUserRole: Calling /users/me endpoint');
      
      const response = await fetch(`${process.env.REACT_APP_API_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('🔍 checkUserRole: Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ checkUserRole: Error response:', response.status, errorText);
        console.error('❌ checkUserRole: Token (first 50 chars):', token?.substring(0, 50));
        
        // Don't fail silently - this is causing the redirect loop
        // Just set admin to false and continue
        setIsAdmin(false);
        return;
      }
      
      const data = await response.json();
      console.log('✅ checkUserRole: Success, is_admin:', data?.is_admin);
      setIsAdmin(data?.is_admin || false);
    } catch (error) {
      console.error('❌ checkUserRole: Exception:', error);
      setIsAdmin(false);
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      console.log('Attempting to sign in with email:', email);
      console.log('Supabase URL:', process.env.REACT_APP_SUPABASE_URL);
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      console.log('Sign in response:', { data, error });

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
  };

  const signOut = async () => {
    try {
      console.log('🚪 Signing out - clearing all session data');
      
      // Sign out from Supabase (clears tokens and local storage)
      await supabase.auth.signOut();
      
      // Clear local state
      setSession(null);
      setUser(null);
      setIsAdmin(false);
      
      console.log('✅ Sign out complete');
    } catch (error) {
      console.error('❌ Error signing out:', error);
    }
  };

  const refreshSession = async () => {
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
  };

  const value = {
    session,
    user,
    loading,
    signIn,
    signOut,
    refreshSession,
    isAdmin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
