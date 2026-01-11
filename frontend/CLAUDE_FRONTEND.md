# Frontend Development Guide - AI Web Scraper

> **Purpose**: Frontend-specific conventions, patterns, and best practices for React/TypeScript development on this project.

---

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript 4.9+
- **Build Tool**: Create React App
- **Routing**: React Router v6
- **Styling**: TailwindCSS + shadcn/ui
- **State Management**: React Context API (AuthContext)
- **HTTP Client**: Axios
- **Auth**: Supabase Auth (JWT tokens)

---

## Architecture Overview

```
frontend/src/
├── components/        # Reusable UI components
│   ├── Layout.tsx    # Main layout wrapper
│   ├── Footer.tsx    # Site footer
│   ├── Navbar.tsx    # Navigation bar
│   └── ...           # Other shared components
├── contexts/          # React Context
│   └── AuthContext.tsx  # Authentication state
├── pages/            # Route pages
│   ├── DashboardPage.tsx
│   ├── CrawlsPage.tsx
│   ├── CrawlDetailPage.tsx
│   └── ...
├── services/         # API clients
│   └── api.ts       # Axios client and API methods
├── utils/           # Utility functions
├── App.tsx          # Main app component (routes)
└── index.tsx        # React entry point
```

---

## Critical Patterns

### 1. File Naming - Case Sensitivity

**CRITICAL**: File names must match imports EXACTLY (Windows is case-insensitive, but CI/CD may not be).

**✅ Correct**:
```typescript
// File: SignUpPage.tsx
import SignUpPage from './pages/SignUpPage';
```

**❌ Wrong** (will fail):
```typescript
// File: SignUpPage.tsx
import SignupPage from './pages/Signuppage';  // Case mismatch!
```

**Convention**:
- **Components**: PascalCase (e.g., `CrawlDetailPage.tsx`)
- **Utilities**: camelCase (e.g., `formatDate.ts`)
- **Constants**: SCREAMING_SNAKE_CASE (e.g., `API_CONSTANTS.ts`)

---

### 2. Protected Routes Pattern

**All authenticated routes use the `ProtectedRoute` wrapper**:

```typescript
// In App.tsx
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

// Usage
<Route path="crawls" element={<ProtectedRoute element={<CrawlsPage />} />} />
<Route path="users" element={<ProtectedRoute element={<UsersPage />} adminOnly={true} />} />
```

**Key points**:
- Check loading state first (avoid flash of wrong content)
- Redirect to `/login` if not authenticated
- Check `isAdmin` for admin-only routes
- Use `replace` to avoid navigation history pollution

---

### 3. API Client Pattern

**Centralized API client in `services/api.ts`**:

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to all requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('supabase.auth.token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // API methods
  async getCrawls() {
    const response = await this.client.get('/crawls');
    return response.data;
  }

  async getCrawl(id: string) {
    const response = await this.client.get(`/crawls/${id}`);
    return response.data;
  }

  async createCrawl(data: CrawlCreate) {
    const response = await this.client.post('/crawls', data);
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;
```

**Usage in components**:
```typescript
import apiService from '../services/api';

const CrawlsPage: React.FC = () => {
  const [crawls, setCrawls] = useState([]);

  useEffect(() => {
    const fetchCrawls = async () => {
      try {
        const data = await apiService.getCrawls();
        setCrawls(data);
      } catch (error) {
        console.error('Error fetching crawls:', error);
        toast.error('Failed to load crawls');
      }
    };

    fetchCrawls();
  }, []);

  // ...
};
```

---

### 4. Authentication Context

**AuthContext provides user state globally**:

```typescript
// contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAdmin: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  // Initialize auth state
  useEffect(() => {
    const session = supabase.auth.getSession();
    // ... fetch user, check admin status
  }, []);

  // ... auth methods

  return (
    <AuthContext.Provider value={{ user, loading, isAdmin, signIn, signOut, signUp }}>
      {children}
    </AuthContext.Provider>
  );
};

// Usage hook
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

**Usage in components**:
```typescript
import { useAuth } from '../contexts/AuthContext';

const NavBar: React.FC = () => {
  const { user, isAdmin, signOut } = useAuth();

  return (
    <nav>
      <span>Welcome, {user?.email}</span>
      {isAdmin && <Link to="/users">Users</Link>}
      <button onClick={signOut}>Logout</button>
    </nav>
  );
};
```

---

### 5. Toast Notifications

**Using `sonner` for toast messages**:

```typescript
import { toast } from 'sonner';

// Success
toast.success('Crawl created successfully!');

// Error
toast.error('Failed to create crawl');

// Info
toast.info('Processing...');

// Warning
toast.warning('Crawl is taking longer than expected');

// Custom
toast('Custom message', {
  description: 'Additional details here',
  action: {
    label: 'Undo',
    onClick: () => console.log('Undo'),
  },
});
```

**Configuration** (in `App.tsx`):
```typescript
<Toaster
  position="top-right"
  richColors
  closeButton
  expand={false}
  duration={4000}
/>
```

---

### 6. Loading States

**Pattern**: Show loading UI while fetching data.

```typescript
const [loading, setLoading] = useState(true);
const [data, setData] = useState(null);
const [error, setError] = useState(null);

useEffect(() => {
  const fetchData = async () => {
    try {
      setLoading(true);
      const result = await apiService.getData();
      setData(result);
    } catch (err) {
      setError(err.message);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  fetchData();
}, []);

if (loading) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  );
}

if (error) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-red-600">Error: {error}</div>
    </div>
  );
}

return <div>{/* Render data */}</div>;
```

---

### 7. Form Handling

**Pattern**: Controlled components with validation.

```typescript
const [formData, setFormData] = useState({
  url: '',
  maxDepth: 2,
  maxPages: 100,
});
const [errors, setErrors] = useState<Record<string, string>>({});
const [submitting, setSubmitting] = useState(false);

const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const { name, value, type, checked } = e.target;
  setFormData(prev => ({
    ...prev,
    [name]: type === 'checkbox' ? checked : value,
  }));
  // Clear error for this field
  if (errors[name]) {
    setErrors(prev => ({ ...prev, [name]: '' }));
  }
};

const validateForm = () => {
  const newErrors: Record<string, string> = {};

  if (!formData.url) {
    newErrors.url = 'URL is required';
  } else if (!formData.url.startsWith('http')) {
    newErrors.url = 'URL must start with http:// or https://';
  }

  if (formData.maxDepth < 1) {
    newErrors.maxDepth = 'Max depth must be at least 1';
  }

  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!validateForm()) {
    return;
  }

  try {
    setSubmitting(true);
    await apiService.createCrawl(formData);
    toast.success('Crawl created successfully!');
    navigate('/crawls');
  } catch (error) {
    toast.error('Failed to create crawl');
  } finally {
    setSubmitting(false);
  }
};

return (
  <form onSubmit={handleSubmit}>
    <input
      name="url"
      value={formData.url}
      onChange={handleChange}
      className={errors.url ? 'border-red-500' : ''}
    />
    {errors.url && <p className="text-red-500 text-sm">{errors.url}</p>}

    <button type="submit" disabled={submitting}>
      {submitting ? 'Creating...' : 'Create Crawl'}
    </button>
  </form>
);
```

---

### 8. Styling with TailwindCSS

**Conventions**:
- Use Tailwind utility classes
- Group related utilities together
- Responsive classes after base classes
- State variants last

**Good**:
```typescript
<button className="
  px-4 py-2                           // Spacing
  bg-blue-600 hover:bg-blue-700       // Colors
  text-white font-medium              // Typography
  rounded-lg shadow-sm                // Borders
  transition-colors duration-200      // Animations
  disabled:opacity-50 disabled:cursor-not-allowed  // States
  md:px-6 md:py-3                    // Responsive
">
  Submit
</button>
```

**Color palette** (use these consistently):
- Primary: `primary-{50-900}` (Blue)
- Secondary: `secondary-{50-900}` (Orange)
- Gray: `gray-{50-900}`
- Red: `red-{50-900}` (Errors)
- Green: `green-{50-900}` (Success)
- Yellow: `yellow-{50-900}` (Warnings)

---

## Page-Specific Patterns

### CrawlDetailPage.tsx

**Key responsibilities**:
- Display crawl metadata and status
- Show tabs for Pages, Links, Images, Issues
- Handle rerun, stop, delete actions
- Calculate duration and format timestamps

**Important functions**:
```typescript
const calculateDuration = (startDate: string, endDate?: string) => {
  if (!endDate) return 'In progress...';

  const start = new Date(startDate);
  const end = new Date(endDate);
  const durationMs = end.getTime() - start.getTime();

  const hours = Math.floor(durationMs / 3600000);
  const minutes = Math.floor((durationMs % 3600000) / 60000);
  const seconds = Math.floor((durationMs % 60000) / 1000);

  if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
};

const handleRerun = async () => {
  if (!crawl) return;
  setRerunning(true);

  try {
    // Create new crawl with incremented counter
    const newName = `${baseName} #${nextNumber} - ${timestamp}`;
    await apiService.createCrawl({
      ...crawl,
      name: newName,
    });
    toast.success('Crawl re-run started');
    navigate('/crawls');
  } catch (error) {
    toast.error('Failed to re-run crawl');
  } finally {
    setRerunning(false);
  }
};
```

**Key state**:
- `activeTab`: Which tab is currently visible
- `crawl`: Crawl metadata
- `pages/links/images/issues`: Tab content
- `filters`: Status filters, sort options

---

### DocsPage.tsx

**Key responsibilities**:
- Display documentation sidebar and content
- Auto-load Platform Overview on page load
- Render Markdown-formatted documentation
- Show footer at bottom

**Important state**:
```typescript
const [activeSection, setActiveSection] = useState<string>('overview');  // Auto-load Platform Overview
const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['introduction']));
```

**Layout pattern**:
```typescript
return (
  <div className="min-h-screen bg-gray-50 flex flex-col">
    <div className="flex-grow">
      {/* Sidebar and content */}
    </div>
    <Footer />  {/* Footer always at bottom */}
  </div>
);
```

---

## Component Patterns

### Layout Wrapper

**Pattern**: Wrap all protected pages in Layout component.

```typescript
// components/Layout.tsx
const Layout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow">
        <Outlet />  {/* Child routes render here */}
      </main>
      <Footer />
    </div>
  );
};

// In App.tsx
<Route path="/" element={<Layout />}>
  <Route index element={<MarketingHomePage />} />
  <Route path="dashboard" element={<ProtectedRoute element={<DashboardPage />} />} />
  {/* ... more routes */}
</Route>
```

---

### Modal Dialogs

**Pattern**: Use modal for confirmations.

```typescript
<ConfirmationModal
  isOpen={showDeleteConfirm}
  onClose={() => setShowDeleteConfirm(false)}
  onConfirm={handleDelete}
  title="Delete Crawl"
  message={`Are you sure you want to delete "${crawl.name}"? This action cannot be undone.`}
  confirmText="Delete Crawl"
  variant="danger"
  isLoading={deleting}
/>
```

---

### Table with Filters

**Pattern**: Filterable, sortable tables.

```typescript
const [filter, setFilter] = useState<'all' | 'internal' | 'external'>('all');
const [sort, setSort] = useState<{ field: string; direction: 'asc' | 'desc' }>({
  field: 'anchor_text',
  direction: 'asc',
});

const filteredData = useMemo(() => {
  let result = data;

  // Apply filters
  if (filter === 'internal') {
    result = result.filter(item => item.is_internal);
  } else if (filter === 'external') {
    result = result.filter(item => !item.is_internal);
  }

  // Apply sort
  result = result.sort((a, b) => {
    const aVal = a[sort.field];
    const bVal = b[sort.field];
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
    return 0;
  });

  return result;
}, [data, filter, sort]);
```

---

## TypeScript Best Practices

### Type Definitions

**Define interfaces for all data structures**:

```typescript
interface Crawl {
  id: string;
  user_id: string;
  url: string;
  name: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'stopped';
  created_at: string;
  completed_at?: string;  // Optional
  max_depth: number;
  max_pages: number;
  pages_crawled: number;
}

interface CrawlCreate {
  url: string;
  name?: string;
  max_depth?: number;
  max_pages?: number;
  respect_robots_txt?: boolean;
  follow_external_links?: boolean;
  js_rendering?: boolean;
}

interface Page {
  id: string;
  crawl_id: string;
  url: string;
  status_code?: number;
  title?: string;
  created_at: string;
}
```

### Props Typing

**Always type component props**:

```typescript
interface CrawlCardProps {
  crawl: Crawl;
  onDelete: (id: string) => void;
  onRerun: (id: string) => void;
}

const CrawlCard: React.FC<CrawlCardProps> = ({ crawl, onDelete, onRerun }) => {
  // ...
};
```

### Event Handlers

**Type event handlers properly**:

```typescript
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  // ...
};

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  // ...
};

const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  // ...
};
```

---

## Environment Variables

**`.env` structure**:
```bash
# Supabase
REACT_APP_SUPABASE_URL=https://xxx.supabase.co
REACT_APP_SUPABASE_PUBLISHABLE_KEY=eyJhbGc...  # Public key (RLS enforced)

# API
REACT_APP_API_URL=http://localhost:8000/api/v1

# Optional: Analytics
REACT_APP_GA_TRACKING_ID=UA-XXXXX-X
```

**Access via**:
```typescript
const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
```

**IMPORTANT**: Prefix all custom variables with `REACT_APP_` (Create React App requirement).

---

## Performance Optimization

### Memoization

**Use `useMemo` for expensive computations**:

```typescript
const filteredData = useMemo(() => {
  return data.filter(item => item.status === filter);
}, [data, filter]);  // Only recompute when data or filter changes
```

**Use `useCallback` for functions passed to child components**:

```typescript
const handleDelete = useCallback((id: string) => {
  // ... delete logic
}, []);  // Function reference stays stable

<ChildComponent onDelete={handleDelete} />  // Won't cause unnecessary re-renders
```

### Code Splitting

**Lazy load routes**:

```typescript
import { lazy, Suspense } from 'react';

const CrawlDetailPage = lazy(() => import('./pages/CrawlDetailPage'));

<Suspense fallback={<LoadingSpinner />}>
  <Route path="crawls/:id" element={<CrawlDetailPage />} />
</Suspense>
```

---

## Accessibility

### ARIA Labels

**Add labels for screen readers**:

```typescript
<button
  onClick={handleDelete}
  aria-label="Delete crawl"
  className="text-red-600"
>
  <TrashIcon className="h-5 w-5" />
</button>
```

### Keyboard Navigation

**Ensure interactive elements are keyboard accessible**:

```typescript
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  className="cursor-pointer"
>
  Click me
</div>
```

---

## Testing (Future Consideration)

### Component Tests

**Pattern** (when implemented):

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import CrawlCard from './CrawlCard';

test('renders crawl name', () => {
  const crawl = { name: 'Test Crawl', status: 'completed', /* ... */ };
  render(<CrawlCard crawl={crawl} onDelete={() => {}} onRerun={() => {}} />);

  expect(screen.getByText('Test Crawl')).toBeInTheDocument();
});

test('calls onDelete when delete button clicked', () => {
  const handleDelete = jest.fn();
  const crawl = { id: '123', /* ... */ };

  render(<CrawlCard crawl={crawl} onDelete={handleDelete} onRerun={() => {}} />);

  fireEvent.click(screen.getByLabelText('Delete crawl'));
  expect(handleDelete).toHaveBeenCalledWith('123');
});
```

---

## Code Review Checklist

Before committing frontend code:

- [ ] File names match imports exactly (case-sensitive)
- [ ] All props typed with TypeScript interfaces
- [ ] Loading states shown while fetching data
- [ ] Error handling with toast notifications
- [ ] Forms validate input before submission
- [ ] Protected routes use `ProtectedRoute` wrapper
- [ ] API calls use centralized `apiService`
- [ ] TailwindCSS utilities used (no inline styles)
- [ ] Responsive classes added for mobile (`md:`, `lg:`)
- [ ] Accessibility attributes added (aria-labels, etc.)
- [ ] No console.log statements left in code
- [ ] Environment variables prefixed with `REACT_APP_`

---

## Common Pitfalls

### Pitfall #1: Case-Sensitive Imports

**Problem**: `import SignupPage from './pages/Signuppage'` (file is `SignUpPage.tsx`)

**Solution**: Match file name exactly, including case.

### Pitfall #2: Forgetting to Show Loading State

**Problem**: Page flashes error before data loads

**Solution**: Check `loading` state before rendering content.

### Pitfall #3: Not Clearing Form Errors

**Problem**: Error message persists after user fixes input

**Solution**: Clear error when input changes:
```typescript
const handleChange = (e) => {
  setFormData({ ...formData, [e.target.name]: e.target.value });
  setErrors({ ...errors, [e.target.name]: '' });  // Clear error
};
```

### Pitfall #4: Missing Dependencies in useEffect

**Problem**: stale closure, outdated data

**Solution**: Add all dependencies to dependency array:
```typescript
useEffect(() => {
  fetchData(userId);
}, [userId]);  // Include userId!
```

---

**Last Updated**: January 10, 2026
**Maintained By**: Claude (Anthropic) + CushLabs Team