/// <reference types="react-scripts" />

// Add type definitions for environment variables
declare namespace NodeJS {
  interface ProcessEnv {
    REACT_APP_API_URL: string;
    REACT_APP_SUPABASE_URL: string;
    REACT_APP_SUPABASE_PUBLISHABLE_KEY?: string;
    REACT_APP_SUPABASE_ANON_KEY?: string;
  }
}
