import { supabase } from '../lib/supabase';

export const testSupabaseConnection = async () => {
  try {
    console.log('Testing Supabase connection...');
    
    // Test basic connection
    const { data, error } = await supabase.from('users').select('count', { count: 'exact', head: true });
    
    if (error) {
      console.error('Supabase connection error:', error);
      return { success: false, error: error.message };
    }
    
    console.log('Supabase connection successful');
    return { success: true, data };
  } catch (error) {
    console.error('Connection test failed:', error);
    return { success: false, error: (error as Error).message };
  }
};

export const createTestUser = async (email: string, password: string) => {
  try {
    console.log('Creating test user...');
    
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });
    
    if (error) {
      console.error('User creation error:', error);
      return { success: false, error: error.message };
    }
    
    console.log('Test user created successfully:', data);
    return { success: true, data };
  } catch (error) {
    console.error('User creation failed:', error);
    return { success: false, error: (error as Error).message };
  }
};
