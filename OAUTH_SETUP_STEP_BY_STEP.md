# OAuth Setup - Complete Step-by-Step Guide

## 🎯 Goal
Enable "Sign in with Google" and "Sign in with GitHub" on your login page.

---

## 📋 Prerequisites
- [ ] Supabase project created
- [ ] Google account
- [ ] GitHub account

---

## Part 1: Google OAuth Setup (15 minutes)

### Step 1: Get Your Supabase Callback URL

1. Open [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Look at your browser URL - it will be something like:
   ```
   https://app.supabase.com/project/abcdefghijklmno
   ```
4. The part after `/project/` is your **Project ID**: `abcdefghijklmno`

5. Your Supabase callback URL is:
   ```
   https://abcdefghijklmno.supabase.co/auth/v1/callback
   ```

   **Copy this URL - you'll need it multiple times!**

---

### Step 2: Create Google OAuth App

1. Go to [Google Cloud Console](https://console.cloud.google.com/)

2. Click the project dropdown at the top (next to "Google Cloud")

3. Click **"NEW PROJECT"** (top right of the modal)
   - Project name: `AI WebScraper`
   - Click **"CREATE"**

4. Wait for project to be created (30 seconds)

5. Make sure your new project is selected (check top bar)

---

### Step 3: Configure OAuth Consent Screen

1. In left sidebar, click **"APIs & Services"** > **"OAuth consent screen"**

2. Select **"External"** (unless you have Google Workspace)

3. Click **"CREATE"**

4. Fill in **App information**:
   - **App name**: `AI WebScraper`
   - **User support email**: Your email (select from dropdown)
   - **App logo**: (optional - skip for now)

5. Scroll to **Developer contact information**:
   - **Email addresses**: Your email

6. Click **"SAVE AND CONTINUE"**

7. **Scopes page** - Click **"ADD OR REMOVE SCOPES"**
   - Find and check:
     - `.../auth/userinfo.email`
     - `.../auth/userinfo.profile`
     - `openid`
   - Click **"UPDATE"**
   - Click **"SAVE AND CONTINUE"**

8. **Test users** - Click **"SAVE AND CONTINUE"** (skip for now)

9. **Summary** - Click **"BACK TO DASHBOARD"**

---

### Step 4: Create OAuth 2.0 Credentials

1. In left sidebar, click **"Credentials"**

2. Click **"CREATE CREDENTIALS"** (top of page) > **"OAuth client ID"**

3. **Application type**: Select **"Web application"**

4. **Name**: `AI WebScraper Web Client`

5. **Authorized JavaScript origins** - Click **"ADD URI"**
   - Add: `http://localhost:3000`
   - Click **"ADD URI"** again
   - Add: `http://localhost:5173`
   - Click **"ADD URI"** again
   - Add your production URL (if you have one): `https://yourdomain.com`

6. **Authorized redirect URIs** - Click **"ADD URI"**
   - Add your Supabase callback URL from Step 1:
     ```
     https://YOUR-PROJECT-ID.supabase.co/auth/v1/callback
     ```
   - **Replace YOUR-PROJECT-ID** with your actual project ID!

7. Click **"CREATE"**

8. **IMPORTANT:** A modal will appear with your credentials:
   - **Client ID**: Starts with something like `123456789-abc.apps.googleusercontent.com`
   - **Client secret**: Random string like `GOCSPX-abc123xyz`

   **Keep this modal open** or copy both to a text file!

---

### Step 5: Configure Google OAuth in Supabase

1. Go back to [Supabase Dashboard](https://app.supabase.com/)

2. In left sidebar, click **"Authentication"**

3. Click **"Providers"** (under Configuration)

4. Scroll down and find **"Google"**

5. Toggle the switch to **"Enabled"** (right side)

6. Paste your credentials:
   - **Client ID (for OAuth)**: Paste from Google Console
   - **Client Secret (for OAuth)**: Paste from Google Console

7. **Authorize redirect URI** (optional): Leave default or verify it matches:
   ```
   https://YOUR-PROJECT-ID.supabase.co/auth/v1/callback
   ```

8. Click **"Save"** (bottom right)

---

### Step 6: Test Google OAuth

1. Open your project in VS Code

2. Make sure frontend is running:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open browser to `http://localhost:3000/login`

4. Click **"Continue with Google"** button

5. **Expected flow:**
   - Redirects to Google sign-in
   - Choose your Google account
   - Click "Continue" to authorize
   - Redirects back to `http://localhost:3000/dashboard`
   - You should be logged in!

6. **If error occurs:**
   - `redirect_uri_mismatch`: Go back to Google Console, check redirect URI exactly matches Supabase callback
   - `invalid_client`: Check Client ID and Secret in Supabase
   - `access_denied`: User cancelled - this is normal

---

## Part 2: GitHub OAuth Setup (10 minutes)

### Step 1: Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)

2. Click **"OAuth Apps"** (left sidebar)

3. Click **"New OAuth App"** (top right)

4. Fill in the form:
   - **Application name**: `AI WebScraper`
   - **Homepage URL**: `http://localhost:3000`
   - **Application description**: `AI-powered website crawler and SEO analyzer` (optional)
   - **Authorization callback URL**:
     ```
     https://YOUR-PROJECT-ID.supabase.co/auth/v1/callback
     ```
     **Use the same Supabase callback URL from Part 1, Step 1!**

5. Click **"Register application"**

---

### Step 2: Get GitHub Client Credentials

1. You should now see your app details

2. Copy the **Client ID** (looks like: `Iv1.a1b2c3d4e5f6g7h8`)

3. Click **"Generate a new client secret"**

4. **Confirm your password** if prompted

5. **IMPORTANT:** Copy the **Client secret** immediately!
   - It looks like: `1234567890abcdef1234567890abcdef12345678`
   - **You can only see this ONCE!**
   - If you lose it, you'll need to generate a new one

---

### Step 3: Configure GitHub OAuth in Supabase

1. Go back to [Supabase Dashboard](https://app.supabase.com/)

2. **Authentication** > **Providers**

3. Scroll down and find **"GitHub"**

4. Toggle the switch to **"Enabled"**

5. Paste your credentials:
   - **Client ID (for OAuth)**: Paste from GitHub
   - **Client Secret (for OAuth)**: Paste from GitHub

6. Click **"Save"**

---

### Step 4: Test GitHub OAuth

1. Go to `http://localhost:3000/login`

2. Click **"Continue with GitHub"** button

3. **Expected flow:**
   - Redirects to GitHub authorization
   - Click "Authorize [your-username]"
   - Redirects back to `http://localhost:3000/dashboard`
   - You should be logged in!

4. **If error occurs:**
   - `redirect_uri_mismatch`: Check callback URL in GitHub app settings
   - `Application suspended`: Contact GitHub support or check app status
   - `access_denied`: User cancelled - this is normal

---

## 🎉 Success Checklist

After completing both setups, verify:

- [ ] "Continue with Google" button works
- [ ] "Continue with GitHub" button works
- [ ] After OAuth login, user lands on `/dashboard`
- [ ] User data appears in Supabase Auth > Users
- [ ] Can sign in from incognito/private window
- [ ] Can log out and log back in

---

## 🚨 Troubleshooting

### Google OAuth Issues

**Error: redirect_uri_mismatch**
```
Solution:
1. Go to Google Cloud Console > Credentials
2. Click your OAuth 2.0 Client ID
3. Verify "Authorized redirect URIs" contains:
   https://YOUR-PROJECT-ID.supabase.co/auth/v1/callback
4. Save and try again
```

**Error: invalid_client**
```
Solution:
1. Go to Supabase > Authentication > Providers > Google
2. Re-check Client ID and Client Secret
3. Make sure there are no extra spaces
4. Save and try again
```

**Error: access_blocked**
```
Solution:
1. Go to Google Cloud Console > OAuth consent screen
2. Add your test email to "Test users"
3. Or publish your app (if ready for production)
```

---

### GitHub OAuth Issues

**Error: redirect_uri_mismatch**
```
Solution:
1. Go to GitHub > Settings > Developer settings > OAuth Apps
2. Click your app
3. Update "Authorization callback URL" to:
   https://YOUR-PROJECT-ID.supabase.co/auth/v1/callback
4. Save and try again
```

**Error: Application suspended**
```
Solution:
1. Check your GitHub app status
2. Contact GitHub support if needed
3. Create a new OAuth app as a workaround
```

**Button does nothing / no redirect**
```
Solution:
1. Open browser console (F12)
2. Click GitHub button again
3. Check for error messages
4. Verify Supabase is enabled for GitHub provider
```

---

## 📱 Production Setup (When Ready)

When you deploy to production, you'll need to update:

### Google Cloud Console:
1. Go to Credentials > Your OAuth Client
2. Add production domain to **Authorized JavaScript origins**:
   ```
   https://yourdomain.com
   ```
3. Callback URI stays the same (Supabase callback)

### GitHub OAuth App:
1. Go to your OAuth App settings
2. Update **Homepage URL** to:
   ```
   https://yourdomain.com
   ```
3. Callback URI stays the same (Supabase callback)

### Supabase:
1. Go to **Authentication** > **URL Configuration**
2. Update **Site URL** to your production domain
3. OAuth providers will continue working automatically

---

## 🔐 Security Notes

- ✅ OAuth secrets are stored in Supabase (server-side)
- ✅ Frontend only receives tokens, never secrets
- ✅ Supabase handles token refresh automatically
- ⚠️ Never put Client Secrets in frontend `.env` files
- ⚠️ Never commit secrets to GitHub
- ⚠️ Service role key should only be in backend

---

## 📞 Need Help?

Common places to check:
1. **Supabase Dashboard** > Authentication > Users (see if user was created)
2. **Browser Console** (F12) > Network tab (see API calls)
3. **Supabase Logs** > Dashboard > Logs (see auth attempts)

If still stuck:
- Check [Supabase Discord](https://discord.supabase.com/)
- Post on [Supabase GitHub Discussions](https://github.com/orgs/supabase/discussions)

---

## ✅ Final Verification

Run through this checklist to confirm everything works:

### Google OAuth:
- [ ] Can sign in from Chrome
- [ ] Can sign in from incognito
- [ ] User created in Supabase Auth > Users
- [ ] Email matches Google account
- [ ] Avatar URL populated (if using)

### GitHub OAuth:
- [ ] Can sign in from any browser
- [ ] Can sign in from incognito
- [ ] User created in Supabase Auth > Users
- [ ] Username matches GitHub account
- [ ] Avatar URL populated

### Both:
- [ ] After login, redirects to `/dashboard`
- [ ] Can log out and log back in
- [ ] User data persists between sessions
- [ ] No errors in browser console
- [ ] No errors in Supabase logs

---

## 🎊 You're Done!

Your app now has professional OAuth authentication!

**Next steps:**
- Test on mobile devices
- Add production domains when ready to deploy
- Consider adding more providers (Microsoft, Apple, etc.)

**What we implemented:**
- ✅ Google OAuth login
- ✅ GitHub OAuth login
- ✅ Secure authentication flow
- ✅ Automatic user creation in Supabase
- ✅ Session management

Great work! 🚀
