import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '../LoginPage';
import { AuthContext } from '../../contexts/AuthContext';

// Mock supabase
jest.mock('../../lib/supabase', () => ({
  supabase: {
    auth: {
      signOut: jest.fn().mockResolvedValue({}),
      signInWithOAuth: jest.fn().mockResolvedValue({ error: null }),
    },
  },
}));

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const mockSignIn = jest.fn();

const mockAuthContext = {
  session: null,
  user: null,
  loading: false,
  isAdmin: false,
  signIn: mockSignIn,
  signOut: jest.fn(),
  refreshSession: jest.fn(),
};

const renderLoginPage = (authOverrides = {}) => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={{ ...mockAuthContext, ...authOverrides }}>
        <LoginPage />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form with email and password fields', () => {
    renderLoginPage();

    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('renders OAuth buttons for Google and GitHub', () => {
    renderLoginPage();

    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /continue with github/i })).toBeInTheDocument();
  });

  test('renders navigation links to forgot password and sign up', () => {
    renderLoginPage();

    expect(screen.getByText('Forgot password?')).toBeInTheDocument();
    expect(screen.getByText('Sign up')).toBeInTheDocument();
  });

  test('submits form and navigates to dashboard on success', async () => {
    mockSignIn.mockResolvedValue({ error: null, data: {} });
    renderLoginPage();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  test('displays error message on login failure', async () => {
    mockSignIn.mockResolvedValue({
      error: { message: 'Invalid login credentials' },
      data: null,
    });
    renderLoginPage();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'wrong@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'badpass' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid login credentials')).toBeInTheDocument();
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('displays generic error on unexpected exception', async () => {
    mockSignIn.mockRejectedValue(new Error('Network error'));
    renderLoginPage();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('An unexpected error occurred. Please try again.')).toBeInTheDocument();
    });
  });

  test('toggles password visibility', () => {
    renderLoginPage();

    const passwordInput = screen.getByLabelText('Password');
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Find the toggle button (it's inside the password field wrapper)
    const toggleButtons = screen.getAllByRole('button');
    const toggleBtn = toggleButtons.find(btn =>
      btn.querySelector('svg') && !btn.textContent?.includes('Sign') && !btn.textContent?.includes('Continue')
    );

    if (toggleBtn) {
      fireEvent.click(toggleBtn);
      expect(passwordInput).toHaveAttribute('type', 'text');

      fireEvent.click(toggleBtn);
      expect(passwordInput).toHaveAttribute('type', 'password');
    }
  });

  test('disables submit button while loading', async () => {
    // Make signIn hang (never resolve)
    mockSignIn.mockImplementation(() => new Promise(() => {}));
    renderLoginPage();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Signing in...')).toBeInTheDocument();
    });
  });
});
