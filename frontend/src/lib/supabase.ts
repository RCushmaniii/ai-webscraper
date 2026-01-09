import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabasePublishableKey = process.env.REACT_APP_SUPABASE_PUBLISHABLE_KEY;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
const supabaseKey = supabasePublishableKey || supabaseAnonKey;

// Debug logging to verify which key is being used
console.log('🔑 Supabase Client Configuration:');
console.log('URL:', supabaseUrl);
console.log('PUBLISHABLE_KEY:', supabasePublishableKey ? `${supabasePublishableKey.substring(0, 20)}...` : 'Not set');
console.log('ANON_KEY:', supabaseAnonKey ? `${supabaseAnonKey.substring(0, 20)}...` : 'Not set');
console.log('Using Key:', supabaseKey ? `${supabaseKey.substring(0, 20)}... (${supabasePublishableKey ? 'PUBLISHABLE' : 'ANON'})` : 'MISSING');

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase environment variables. Check your .env file.');
  console.error('REACT_APP_SUPABASE_URL:', supabaseUrl);
  console.error('REACT_APP_SUPABASE_PUBLISHABLE_KEY:', supabasePublishableKey ? 'Present' : 'Missing');
  console.error('REACT_APP_SUPABASE_ANON_KEY (legacy fallback):', supabaseAnonKey ? 'Present' : 'Missing');
}

export const supabase = createClient(
  supabaseUrl || '',
  supabaseKey || '',
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true
    }
  }
);

export type SupabaseClient = typeof supabase;
