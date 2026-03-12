import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';

// Lazy-loaded page imports for code splitting
const MarketingHomePage = lazy(() => import('./pages/MarketingHomePage'));
const QuickStartPage = lazy(() => import('./pages/QuickStartPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const SignupPage = lazy(() => import('./pages/SignupPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const CrawlsPage = lazy(() => import('./pages/CrawlsPage'));
const CrawlNewPage = lazy(() => import('./pages/CrawlNewPage'));
const CrawlDetailPage = lazy(() => import('./pages/CrawlDetailPage'));
const PageDetailPage = lazy(() => import('./pages/PageDetailPage'));
const UsersPage = lazy(() => import('./pages/UsersPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const CookiesPage = lazy(() => import('./pages/CookiesPage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const UseCasesPage = lazy(() => import('./pages/UseCasesPage'));
const DocsPage = lazy(() => import('./pages/DocsPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));
const ImagesPage = lazy(() => import('./pages/ImagesPage'));

// Protected route component
const ProtectedRoute: React.FC<{ element: React.ReactElement; adminOnly?: boolean }> = ({ 
  element, 
  adminOnly = false 
}) => {
  const { user, loading, isAdmin } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (adminOnly && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return element;
};

function AppRoutes() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary-500"></div></div>}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<MarketingHomePage />} />
        <Route path="quick-start" element={<QuickStartPage />} />
        <Route path="dashboard" element={<ProtectedRoute element={<DashboardPage />} />} />
        <Route path="crawls" element={<ProtectedRoute element={<CrawlsPage />} />} />
        <Route path="crawls/new" element={<ProtectedRoute element={<CrawlNewPage />} />} />
        <Route path="crawls/:id" element={<ProtectedRoute element={<CrawlDetailPage />} />} />
        <Route path="crawls/:crawlId/pages/:pageId" element={<ProtectedRoute element={<PageDetailPage />} />} />
        <Route path="crawls/:crawlId/images" element={<ProtectedRoute element={<ImagesPage />} />} />
        <Route path="users" element={<ProtectedRoute element={<UsersPage />} adminOnly={true} />} />
        <Route path="profile" element={<ProtectedRoute element={<ProfilePage />} />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="use-cases" element={<UseCasesPage />} />
        <Route path="docs" element={<DocsPage />} />
        <Route path="privacy" element={<PrivacyPage />} />
        <Route path="terms" element={<TermsPage />} />
        <Route path="cookies" element={<CookiesPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          richColors
          closeButton
          expand={false}
          duration={4000}
        />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
