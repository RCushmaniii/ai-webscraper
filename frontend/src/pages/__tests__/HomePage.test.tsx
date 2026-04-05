import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import HomePage from '../HomePage';
import { AuthContext } from '../../contexts/AuthContext';

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const renderHomePage = (user: any = null) => {
  const authContext = {
    session: null,
    user,
    loading: false,
    isAdmin: false,
    signIn: jest.fn(),
    signOut: jest.fn(),
    refreshSession: jest.fn(),
  };

  return render(
    <BrowserRouter>
      <AuthContext.Provider value={authContext}>
        <HomePage />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('HomePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders main heading and description', () => {
    renderHomePage();

    expect(screen.getByText('Intelligent Website Analysis')).toBeInTheDocument();
    expect(
      screen.getByText(/Extract clean content, analyze SEO health/)
    ).toBeInTheDocument();
  });

  test('renders feature cards', () => {
    renderHomePage();

    expect(screen.getByText('Simple & Fast')).toBeInTheDocument();
    expect(screen.getByText('Deep Insights')).toBeInTheDocument();
  });

  test('renders the 3-step process', () => {
    renderHomePage();

    expect(screen.getByText('Enter URL')).toBeInTheDocument();
    expect(screen.getByText('AI Crawls Site')).toBeInTheDocument();
    expect(screen.getByText('Review & Export')).toBeInTheDocument();
  });

  test('shows "Get Started" button for unauthenticated users', () => {
    renderHomePage(null);

    expect(screen.getByText('Get Started')).toBeInTheDocument();
    expect(screen.getByText(/Already have an account/)).toBeInTheDocument();
    expect(screen.getByText('Sign in')).toBeInTheDocument();
  });

  test('shows "Go to Crawls" button for authenticated users', () => {
    renderHomePage({ id: 'user-1', email: 'test@example.com' });

    expect(screen.getByText('Go to Crawls')).toBeInTheDocument();
    expect(screen.queryByText(/Already have an account/)).not.toBeInTheDocument();
  });

  test('navigates to /login when unauthenticated user clicks CTA', () => {
    renderHomePage(null);

    fireEvent.click(screen.getByText('Get Started'));
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  test('navigates to /crawls when authenticated user clicks CTA', () => {
    renderHomePage({ id: 'user-1', email: 'test@example.com' });

    fireEvent.click(screen.getByText('Go to Crawls'));
    expect(mockNavigate).toHaveBeenCalledWith('/crawls');
  });

  test('sets page title', () => {
    renderHomePage();

    expect(document.title).toContain('Home');
  });
});
