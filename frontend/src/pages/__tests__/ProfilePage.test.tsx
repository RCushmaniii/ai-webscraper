import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import ProfilePage from '../ProfilePage';
import { apiService } from '../../services/api';
import { AuthContext } from '../../contexts/AuthContext';

// Mock the API service
jest.mock('../../services/api', () => ({
  apiService: {
    updateUserProfile: jest.fn(),
    updateUserPassword: jest.fn(),
  },
}));

// Mock auth context — provider: 'email' to show password change section
const mockAuthContext = {
  session: null,
  user: {
    id: 'user-123',
    email: 'test@example.com',
    user_metadata: { full_name: 'Test User' },
    app_metadata: { provider: 'email' },
    last_sign_in_at: '2023-08-01T00:00:00Z',
    role: 'admin',
    created_at: '2023-01-01T00:00:00Z',
    aud: 'authenticated',
  } as any,
  loading: false,
  isAdmin: true,
  signIn: jest.fn(),
  signOut: jest.fn(),
  refreshSession: jest.fn(),
};

describe('ProfilePage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderProfilePage = () => {
    return render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <ProfilePage />
        </AuthContext.Provider>
      </BrowserRouter>
    );
  };

  test('renders profile information correctly', () => {
    renderProfilePage();

    expect(screen.getByText('Your Profile')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
  });

  test('allows updating profile information', async () => {
    (apiService.updateUserProfile as jest.Mock).mockResolvedValue({ success: true });

    renderProfilePage();

    const fullNameInput = screen.getByLabelText('Full Name');
    fireEvent.change(fullNameInput, { target: { value: 'Updated Name' } });

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Profile updated successfully')).toBeInTheDocument();
    });

    expect(apiService.updateUserProfile).toHaveBeenCalledWith({
      full_name: 'Updated Name',
    });
    expect(mockAuthContext.refreshSession).toHaveBeenCalled();
  });

  test('shows error message when profile update fails', async () => {
    (apiService.updateUserProfile as jest.Mock).mockRejectedValue(new Error('Update failed'));

    renderProfilePage();

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Failed to update profile. Please try again.')).toBeInTheDocument();
    });
  });

  test('allows changing password with correct current password', async () => {
    (apiService.updateUserPassword as jest.Mock).mockResolvedValue({ success: true });

    renderProfilePage();

    const currentPasswordInput = screen.getByLabelText('Current Password');
    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');

    fireEvent.change(currentPasswordInput, { target: { value: 'currentPass123' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newPass123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'newPass123' } });

    const updatePasswordButton = screen.getByRole('button', { name: /update password/i });
    fireEvent.click(updatePasswordButton);

    await waitFor(() => {
      expect(screen.getByText('Password updated successfully')).toBeInTheDocument();
    });

    expect(apiService.updateUserPassword).toHaveBeenCalledWith({
      current_password: 'currentPass123',
      new_password: 'newPass123',
    });
  });

  test('shows error when passwords do not match', async () => {
    renderProfilePage();

    const currentPasswordInput = screen.getByLabelText('Current Password');
    const newPasswordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');

    fireEvent.change(currentPasswordInput, { target: { value: 'currentPass123' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newPass123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'differentPass' } });

    const updatePasswordButton = screen.getByRole('button', { name: /update password/i });
    fireEvent.click(updatePasswordButton);

    expect(screen.getByText('New passwords do not match')).toBeInTheDocument();
    expect(apiService.updateUserPassword).not.toHaveBeenCalled();
  });
});
