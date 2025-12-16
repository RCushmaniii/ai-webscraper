# Frontend Architecture Documentation

## Overview

The AAA WebScraper frontend is built with React, Vite, and Tailwind CSS, following modern best practices for component design, state management, and code organization. This document outlines the architecture, key components, and usage patterns to help developers understand and contribute to the codebase.

## Technology Stack

- **React**: UI library for building component-based interfaces
- **Vite**: Build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Supabase**: Authentication and database interactions
- **TypeScript**: Static type checking
- **Jest & React Testing Library**: Unit testing

## Directory Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   ├── contexts/        # React contexts for state management
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   │   └── __tests__/   # Page component tests
│   ├── services/        # API and utility services
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Helper functions
│   ├── App.tsx          # Main application component
│   └── main.tsx         # Application entry point
├── docs/                # Documentation
└── tests/               # Test configuration and helpers
```

## Core Architecture Principles

### 1. Single Responsibility Principle (SRP)

Each component, service, and utility has a single responsibility:

- **Components**: Focus on rendering UI and handling user interactions
- **Services**: Handle data fetching, processing, and API communication
- **Contexts**: Manage global state
- **Hooks**: Encapsulate reusable logic

### 2. Separation of Concerns (SoC)

The application is divided into distinct layers:

- **UI/View Layer**: React components in `components/` and `pages/`
- **Logic/State Layer**: Hooks and contexts in `hooks/` and `contexts/`
- **Data Layer**: API services in `services/`

### 3. Component Architecture

Components follow a consistent pattern:

- **Presentational Components**: Focus on UI rendering with props
- **Container Components**: Handle data fetching and state management
- **Page Components**: Compose containers and presentational components

## Key Components and Usage

### Authentication

Authentication is handled through the `AuthContext` which provides:

```typescript
// Usage example
const { user, loading, isAdmin, signIn, signOut, refreshSession } = useAuth();
```

- `user`: Current authenticated user object
- `loading`: Boolean indicating authentication state loading
- `isAdmin`: Boolean indicating if user has admin privileges
- `signIn()`: Function to authenticate a user
- `signOut()`: Function to log out a user
- `refreshSession()`: Function to refresh the user session

### API Service

The `apiService` provides methods for all backend communication:

```typescript
// Usage examples
const users = await apiService.getUsers();
const profile = await apiService.updateUserProfile({ full_name: 'New Name' });
const reportData = await apiService.getReportData('week');
```

Key methods include:
- User management: `getUsers()`, `createUser()`, `deleteUser()`
- Profile management: `updateUserProfile()`, `updateUserPassword()`
- Crawl operations: `getCrawls()`, `createCrawl()`, `getCrawlDetails()`
- Batch operations: `getBatches()`, `createBatch()`, `getBatchDetails()`
- Reporting: `getReportData()`, `getMockReportData()`

### Protected Routes

Routes requiring authentication use the `ProtectedRoute` component:

```typescript
<Route path="dashboard" element={<ProtectedRoute element={<DashboardPage />} />} />
<Route path="users" element={<ProtectedRoute element={<UsersPage />} adminOnly={true} />} />
```

The `adminOnly` prop restricts access to admin users only.

## Page Components

### ProfilePage

Displays and allows editing of user profile information:

- Profile information update form
- Password change form with current password verification
- Account details display

```typescript
// Key state hooks
const [profileData, setProfileData] = useState({ full_name: user?.full_name || '' });
const [passwordData, setPasswordData] = useState({
  current_password: '',
  new_password: '',
  confirm_password: ''
});
```

### ReportingPage

Displays analytics and reporting data:

- Summary cards with key metrics
- Status distribution visualization
- Top issues list
- Recent activity tables
- Date range filtering

```typescript
// Key state hooks
const [reportData, setReportData] = useState<ReportData | null>(null);
const [dateRange, setDateRange] = useState<'week' | 'month' | 'year'>('week');
```

## Error Handling

Error handling follows a consistent pattern:

1. Try/catch blocks around async operations
2. Error state management with React useState
3. User-friendly error messages displayed in the UI
4. Console logging for debugging

```typescript
try {
  // API call or other operation
} catch (err) {
  console.error('Error description:', err);
  setError('User-friendly error message');
} finally {
  setLoading(false);
}
```

## Loading States

Loading states are managed consistently:

1. Loading state initialized with `useState(true)`
2. Set to `false` in the `finally` block of try/catch
3. Loading indicators displayed when state is `true`

## Testing

Components are tested using Jest and React Testing Library:

- Unit tests for individual components
- Mock implementations for API services
- Test coverage for key user interactions
- Snapshot testing for UI stability

## Best Practices

1. **TypeScript Types**: Use explicit types for props, state, and API responses
2. **Component Composition**: Build complex UIs from simple components
3. **Custom Hooks**: Extract reusable logic into custom hooks
4. **Consistent Error Handling**: Follow the error handling pattern
5. **Accessibility**: Ensure all components are accessible
6. **Responsive Design**: Use Tailwind's responsive utilities
7. **Code Splitting**: Lazy load components when appropriate
8. **Performance Optimization**: Memoize expensive calculations and components

## Future Improvements

1. Implement more comprehensive test coverage
2. Add end-to-end tests with Cypress
3. Implement client-side form validation library
4. Add internationalization support
5. Improve accessibility features
6. Implement performance monitoring
