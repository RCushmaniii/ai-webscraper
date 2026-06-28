/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly REACT_APP_API_URL: string;
  readonly REACT_APP_SUPABASE_URL: string;
  readonly REACT_APP_SUPABASE_PUBLISHABLE_KEY?: string;
  readonly REACT_APP_SUPABASE_ANON_KEY?: string;
  readonly REACT_APP_SENTRY_DSN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
