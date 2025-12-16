/// <reference types="vite/client" />

interface ImportMeta {
  env: {
    VITE_SUPABASE_URL: string;
    VITE_SUPABASE_ANON_KEY: string;
    VITE_API_URL: string;
    [key: string]: any;
  };
}
