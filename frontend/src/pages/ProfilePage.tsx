import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';

const ProfilePage: React.FC = () => {
  const { user, refreshSession, isAdmin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  // TODO: API Key Management Feature - Future implementation
  // Will allow users to generate and manage API keys for programmatic access
  // Feature includes: create new keys, view existing keys, revoke keys, set expiration dates
  // const [apiKeys, setApiKeys] = useState<{ id: string; name: string; key: string; created_at: string }[]>([]);
  
  const [notificationSettings, setNotificationSettings] = useState({
    emailOnCrawlComplete: true,
    emailMarketing: false,
  });
  const [profileData, setProfileData] = useState<{
    full_name: string;
    email: string;
    current_password: string;
    new_password: string;
    confirm_password: string;
  }>({
    full_name: user?.user_metadata?.full_name || '',
    email: user?.email || '',
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Detect authentication provider
  const authProvider = user?.app_metadata?.provider || 'email';
  const isSocialLogin = authProvider !== 'email';

  useEffect(() => {
    if (user) {
      setProfileData(prev => ({
        ...prev,
        full_name: user.user_metadata?.full_name || '',
        email: user.email || '',
      }));
    }
  }, [user]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiService.updateUserProfile({
        full_name: profileData.full_name,
      });
      
      setSuccess('Profile updated successfully');
      refreshSession(); // Refresh the user session to get updated metadata
    } catch (err) {
      console.error('Error updating profile:', err);
      setError('Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (profileData.new_password !== profileData.confirm_password) {
      setError('New passwords do not match');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiService.updateUserPassword({
        current_password: profileData.current_password,
        new_password: profileData.new_password,
      });

      setSuccess('Password updated successfully');
      setProfileData(prev => ({
        ...prev,
        current_password: '',
        new_password: '',
        confirm_password: '',
      }));
    } catch (err) {
      console.error('Error updating password:', err);
      setError('Failed to update password. Please check your current password and try again.');
    } finally {
      setLoading(false);
    }
  };

  const copyAccountId = async () => {
    if (user?.id) {
      try {
        await navigator.clipboard.writeText(user.id);
        setCopiedId(true);
        setTimeout(() => setCopiedId(false), 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    }
  };

  const handleDeleteAccount = async () => {
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(true);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await apiService.deleteUser(user!.id);
      setSuccess('Account deleted successfully. Redirecting...');
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (err) {
      console.error('Error deleting account:', err);
      setError('Failed to delete account. Please try again or contact support.');
      setShowDeleteConfirm(false);
    } finally {
      setLoading(false);
    }
  };

  const getProviderDisplayName = (provider: string): string => {
    const providerMap: { [key: string]: string } = {
      'email': 'Email/Password',
      'google': 'Google',
      'github': 'GitHub',
      'gitlab': 'GitLab',
      'azure': 'Azure AD',
    };
    return providerMap[provider] || provider.charAt(0).toUpperCase() + provider.slice(1);
  };

  const truncateId = (id: string): string => {
    if (id.length <= 16) return id;
    return `${id.substring(0, 8)}...${id.substring(id.length - 8)}`;
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg font-medium text-gray-500">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="container px-4 py-8 mx-auto">
      <h1 className="mb-6 text-3xl font-bold text-gray-900">Your Profile</h1>

      {error && (
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 mb-6 text-sm text-green-700 bg-green-100 rounded-md" role="alert">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Profile Information */}
        <div className="p-6 bg-white rounded-lg shadow">
          <h2 className="mb-4 text-xl font-semibold text-gray-800">Profile Information</h2>
          <form onSubmit={handleProfileUpdate}>
            <div className="mb-4">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                type="email"
                name="email"
                id="email"
                value={profileData.email}
                disabled
                className="block w-full px-3 py-2 mt-1 bg-gray-100 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-secondary-500 focus:border-secondary-500"
              />
              <p className="mt-1 text-xs text-gray-500">Email cannot be changed</p>
            </div>

            <div className="mb-4">
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                Full Name
              </label>
              <input
                type="text"
                name="full_name"
                id="full_name"
                required
                value={profileData.full_name}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-secondary-500 focus:border-secondary-500"
              />
            </div>

            <div className="flex items-center justify-between mt-6">
              <div>
                <span className="text-sm text-gray-500">
                  Last login: {user.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString() : 'Never'}
                </span>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex justify-center px-4 py-2 text-sm font-medium text-white bg-secondary-500 border border-transparent rounded-md shadow-sm hover:bg-secondary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>

        {/* Change Password - Only show for email/password users */}
        {!isSocialLogin && (
          <div className="p-6 bg-white rounded-lg shadow">
            <h2 className="mb-4 text-xl font-semibold text-gray-800">Change Password</h2>
            <form onSubmit={handlePasswordChange}>
            <div className="mb-4">
              <label htmlFor="current_password" className="block text-sm font-medium text-gray-700">
                Current Password
              </label>
              <input
                type="password"
                name="current_password"
                id="current_password"
                required
                value={profileData.current_password}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-secondary-500 focus:border-secondary-500"
              />
            </div>

            <div className="mb-4">
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">
                New Password
              </label>
              <input
                type="password"
                name="new_password"
                id="new_password"
                required
                value={profileData.new_password}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-secondary-500 focus:border-secondary-500"
              />
            </div>

            <div className="mb-4">
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
                Confirm New Password
              </label>
              <input
                type="password"
                name="confirm_password"
                id="confirm_password"
                required
                value={profileData.confirm_password}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-secondary-500 focus:border-secondary-500"
              />
            </div>

            <div className="flex justify-end mt-6">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex justify-center px-4 py-2 text-sm font-medium text-white bg-secondary-500 border border-transparent rounded-md shadow-sm hover:bg-secondary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:opacity-50"
              >
                {loading ? 'Updating...' : 'Update Password'}
              </button>
            </div>
          </form>
        </div>
        )}
      </div>

      {/* Account Information */}
      <div className="p-6 mt-6 bg-white rounded-lg shadow">
        <h2 className="mb-4 text-xl font-semibold text-gray-800">Account Information</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Account ID</h3>
            <div className="flex items-center mt-1 gap-2">
              <code className="text-sm text-gray-900 font-mono bg-gray-100 px-2 py-1 rounded">
                {truncateId(user.id)}
              </code>
              <button
                onClick={copyAccountId}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="Copy full ID"
              >
                {copiedId ? (
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Role</h3>
            <p className="mt-1">
              <span className={`inline-flex px-2.5 py-1 text-xs font-semibold rounded-full ${
                isAdmin ? 'bg-purple-100 text-purple-800 ring-1 ring-purple-300' : 'bg-blue-100 text-blue-800'
              }`}>
                {isAdmin ? 'Admin' : 'User'}
              </span>
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Auth Method</h3>
            <p className="mt-1">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${
                isSocialLogin
                  ? 'bg-indigo-100 text-indigo-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {authProvider === 'google' && (
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                )}
                {authProvider === 'github' && (
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                  </svg>
                )}
                {getProviderDisplayName(authProvider)}
              </span>
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Member Since</h3>
            <p className="mt-1 text-gray-900">{new Date(user.created_at).toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric'
            })}</p>
          </div>
        </div>
      </div>

      {/* Usage & Quotas */}
      <div className="p-6 mt-6 bg-white rounded-lg shadow">
        <h2 className="mb-4 text-xl font-semibold text-gray-800">Usage & Quotas</h2>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Current Plan</h3>
              <span className="px-2 py-0.5 text-xs font-semibold bg-secondary-100 text-secondary-800 rounded">
                {isAdmin ? 'Admin' : 'Free'}
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{isAdmin ? 'Unlimited' : 'Free Tier'}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Pages Crawled</h3>
            <div className="flex items-end gap-2">
              <p className="text-2xl font-bold text-gray-900">--</p>
              <span className="text-sm text-gray-500 mb-1">/ {isAdmin ? 'unlimited' : '1,000'}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div className="bg-secondary-500 h-2 rounded-full" style={{ width: '0%' }}></div>
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Active Crawls</h3>
            <div className="flex items-end gap-2">
              <p className="text-2xl font-bold text-gray-900">--</p>
              <span className="text-sm text-gray-500 mb-1">/ {isAdmin ? 'unlimited' : '3'}</span>
            </div>
          </div>
        </div>
        <p className="mt-4 text-xs text-gray-500">
          Usage data is updated periodically. Contact support for detailed analytics.
        </p>
      </div>

      {/* Notification Settings */}
      <div className="p-6 mt-6 bg-white rounded-lg shadow">
        <h2 className="mb-4 text-xl font-semibold text-gray-800">Notification Settings</h2>
        <div className="space-y-4">
          <label className="flex items-center justify-between p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
            <div>
              <p className="text-sm font-medium text-gray-900">Crawl Completion Emails</p>
              <p className="text-xs text-gray-500">Get notified when your crawls finish processing</p>
            </div>
            <input
              type="checkbox"
              checked={notificationSettings.emailOnCrawlComplete}
              onChange={(e) => setNotificationSettings(prev => ({
                ...prev,
                emailOnCrawlComplete: e.target.checked
              }))}
              className="w-5 h-5 text-secondary-500 rounded focus:ring-secondary-500"
            />
          </label>
          <label className="flex items-center justify-between p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
            <div>
              <p className="text-sm font-medium text-gray-900">Product Updates</p>
              <p className="text-xs text-gray-500">Receive updates about new features and improvements</p>
            </div>
            <input
              type="checkbox"
              checked={notificationSettings.emailMarketing}
              onChange={(e) => setNotificationSettings(prev => ({
                ...prev,
                emailMarketing: e.target.checked
              }))}
              className="w-5 h-5 text-secondary-500 rounded focus:ring-secondary-500"
            />
          </label>
        </div>
        <div className="flex justify-end mt-4">
          <button
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
          >
            Save Preferences
          </button>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="p-6 mt-6 bg-white rounded-lg shadow border-2 border-red-200">
        <h2 className="mb-4 text-xl font-semibold text-red-700">Danger Zone</h2>
        <div className="p-4 bg-red-50 rounded-lg">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-medium text-red-800">Delete Account</h3>
              <p className="mt-1 text-xs text-red-600">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
            </div>
            {!showDeleteConfirm ? (
              <button
                onClick={handleDeleteAccount}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                Delete Account
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={loading}
                  className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccount}
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                >
                  {loading ? 'Deleting...' : 'Confirm Delete'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
