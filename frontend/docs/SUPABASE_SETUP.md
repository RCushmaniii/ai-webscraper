# Supabase Authentication Setup Guide

## Current Issue
The application is receiving a **400 Bad Request** error when attempting to authenticate. This typically indicates that the Supabase project needs proper configuration.

## Required Supabase Configuration

### 1. Enable Authentication
In your Supabase dashboard:
1. Go to **Authentication** → **Settings**
2. Ensure **Enable email confirmations** is configured appropriately
3. Set **Site URL** to `http://localhost:3001` (for development)
4. Configure **Redirect URLs** if needed

### 2. Create User Table
The application expects a `users` table with the following structure:

```sql
CREATE TABLE users (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  is_admin BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid() = id);
```

### 3. Create Admin User
Since this is an admin-only application, you need to create at least one admin user:

#### Option A: Via Supabase Dashboard
1. Go to **Authentication** → **Users**
2. Click **Add User**
3. Enter email and password
4. After creation, go to **Table Editor** → **users**
5. Insert a record with the user's ID and set `is_admin = true`

#### Option B: Via SQL
```sql
-- First, create the auth user (this should be done via the dashboard or API)
-- Then insert into users table
INSERT INTO users (id, email, is_admin)
VALUES (
  'USER_UUID_FROM_AUTH_USERS', 
  'admin@example.com', 
  true
);
```

### 4. Environment Variables Check
Ensure your `.env.local` has:
```
REACT_APP_SUPABASE_URL=https://ymxfzmjqfojgmqdqfpbz.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your_anon_key_here
```

## Testing the Setup

### 1. Test Connection
Add this to your browser console after the app loads:
```javascript
// Test basic connection
import('./src/utils/supabaseTest.js').then(module => {
  module.testSupabaseConnection().then(result => console.log(result));
});
```

### 2. Create Test User (if needed)
```javascript
// Create a test admin user
import('./src/utils/supabaseTest.js').then(module => {
  module.createTestUser('admin@test.com', 'password123').then(result => console.log(result));
});
```

## Common Issues & Solutions

### 400 Bad Request
- **Cause**: Authentication not enabled or misconfigured
- **Solution**: Check Authentication settings in Supabase dashboard

### Invalid API Key
- **Cause**: Wrong anon key or expired project
- **Solution**: Verify keys in Supabase dashboard → Settings → API

### No Users Found
- **Cause**: No admin users created
- **Solution**: Create at least one admin user as described above

### RLS Policies
- **Cause**: Row Level Security blocking access
- **Solution**: Ensure proper policies are in place for the users table

## Next Steps

1. **Check Supabase Dashboard**: Verify authentication is enabled
2. **Create Admin User**: Set up at least one admin account
3. **Test Login**: Try logging in with the admin credentials
4. **Check Console**: Look for detailed error messages in browser console

## Debug Information

The application now includes enhanced logging. Check the browser console for:
- Supabase URL confirmation
- Authentication attempt details
- Specific error messages from Supabase

If issues persist, check the Supabase dashboard logs for more detailed error information.
