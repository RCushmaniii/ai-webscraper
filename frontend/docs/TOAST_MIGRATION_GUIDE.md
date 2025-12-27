# Toast Migration Guide

## Overview

This guide shows how to migrate from inline error/message state to Sonner toast notifications.

## Benefits of Toast Notifications

- **Better UX**: Non-intrusive, auto-dismiss notifications
- **Consistent**: Same notification style across the app
- **Cleaner Code**: Less state management, no conditional rendering
- **Rich Features**: Success, error, info, warning, loading states
- **Accessible**: Built-in ARIA labels and keyboard support

## Pages to Migrate

Based on grep results, these pages use inline alerts and should be migrated:

- [x] ✅ SignupPage.tsx (completed as example)
- [ ] LoginPage.tsx
- [ ] ForgotPasswordPage.tsx
- [ ] ResetPasswordPage.tsx
- [ ] CrawlsPage.tsx
- [ ] CrawlDetailPage.tsx
- [ ] ProfilePage.tsx
- [ ] DashboardPage.tsx
- [ ] UsersPage.tsx

## Migration Steps

### 1. Import toast

```typescript
// Before
import React, { useState } from 'react';

// After
import React, { useState } from 'react';
import { toast } from 'sonner';
```

### 2. Remove error/message state

```typescript
// Before
const [error, setError] = useState<string | null>(null);
const [message, setMessage] = useState<string | null>(null);

// After
// Remove these lines completely
```

### 3. Replace setError/setMessage with toast

```typescript
// Before
setError('Failed to load data');
setMessage('Success!');

// After
toast.error('Failed to load data');
toast.success('Success!');
```

### 4. Remove conditional error/message rendering from JSX

```typescript
// Before
{error && (
  <div className="p-4 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
    {error}
  </div>
)}

{message && (
  <div className="p-4 text-sm text-green-700 bg-green-100 rounded-md" role="status">
    {message}
  </div>
)}

// After
// Remove these blocks completely
```

## Toast API Reference

### Basic Usage

```typescript
// Success notification
toast.success('Operation completed successfully!');

// Error notification
toast.error('Something went wrong');

// Info notification
toast.info('Here is some information');

// Warning notification
toast.warning('Please be careful');

// Loading state (with promise)
const promise = fetchData();
toast.promise(promise, {
  loading: 'Loading data...',
  success: 'Data loaded successfully!',
  error: 'Failed to load data',
});
```

### Advanced Usage

```typescript
// Custom duration
toast.success('Message', { duration: 5000 });

// With action button
toast('Event created', {
  action: {
    label: 'Undo',
    onClick: () => console.log('Undo clicked'),
  },
});

// Manual dismiss
const toastId = toast.loading('Processing...');
// Later...
toast.success('Done!', { id: toastId });

// Rich content
toast.success(
  <div>
    <strong>Success!</strong>
    <p>Your changes have been saved.</p>
  </div>
);
```

## Complete Example: CrawlsPage.tsx Migration

### Before (Old Pattern)

```typescript
const CrawlsPage: React.FC = () => {
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const fetchCrawls = async () => {
    try {
      setLoading(true);
      const data = await apiService.getCrawls();
      setCrawls(data);
    } catch (err) {
      setError('Failed to load crawls. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiService.deleteCrawl(id);
      setCrawls(crawls.filter(crawl => crawl.id !== id));
      setMessage('Crawl deleted successfully');
    } catch (err) {
      setError('Failed to delete crawl. Please try again later.');
    }
  };

  return (
    <div>
      {error && (
        <div className="p-4 text-sm text-red-700 bg-red-100 rounded-md">
          {error}
        </div>
      )}
      {message && (
        <div className="p-4 text-sm text-green-700 bg-green-100 rounded-md">
          {message}
        </div>
      )}
      {/* Rest of component */}
    </div>
  );
};
```

### After (Toast Pattern)

```typescript
import { toast } from 'sonner';

const CrawlsPage: React.FC = () => {
  // Remove error and message state

  const fetchCrawls = async () => {
    try {
      setLoading(true);
      const data = await apiService.getCrawls();
      setCrawls(data);
    } catch (err) {
      toast.error('Failed to load crawls. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiService.deleteCrawl(id);
      setCrawls(crawls.filter(crawl => crawl.id !== id));
      toast.success('Crawl deleted successfully');
    } catch (err) {
      toast.error('Failed to delete crawl. Please try again later.');
    }
  };

  return (
    <div>
      {/* Remove error/message divs */}
      {/* Rest of component */}
    </div>
  );
};
```

## Special Cases

### Confirmation Dialogs

For operations requiring user confirmation, keep using `window.confirm()` or create a custom modal:

```typescript
const handleDelete = async (id: string) => {
  if (!window.confirm('Are you sure you want to delete this crawl?')) {
    return;
  }

  try {
    await apiService.deleteCrawl(id);
    toast.success('Crawl deleted successfully');
  } catch (err) {
    toast.error('Failed to delete crawl');
  }
};
```

### Form Validation Errors

For inline form validation, you may still want to show errors next to the field:

```typescript
// Keep field-specific errors for UX
const [fieldErrors, setFieldErrors] = useState({});

// Use toast for form submission errors
const handleSubmit = async () => {
  try {
    await submitForm();
    toast.success('Form submitted successfully!');
  } catch (err) {
    toast.error('Failed to submit form');
  }
};
```

### Loading States with Promises

For async operations, use `toast.promise()`:

```typescript
const createCrawl = async (data: CrawlCreate) => {
  const promise = apiService.createCrawl(data);

  toast.promise(promise, {
    loading: 'Creating crawl...',
    success: 'Crawl created successfully!',
    error: 'Failed to create crawl',
  });

  await promise;
  fetchCrawls(); // Refresh list
};
```

## Migration Checklist (Per Page)

For each page you migrate:

- [ ] Import `toast` from 'sonner'
- [ ] Remove `error` and `message` state declarations
- [ ] Replace all `setError()` calls with `toast.error()`
- [ ] Replace all `setMessage()` calls with `toast.success()`
- [ ] Remove conditional error/message JSX blocks
- [ ] Test all error and success scenarios
- [ ] Verify toast appears in correct position (top-right)
- [ ] Check toast auto-dismisses after 4 seconds

## Testing

After migration, test these scenarios:

1. **Success flows**: Verify success toasts appear
2. **Error flows**: Trigger errors and verify error toasts
3. **Multiple toasts**: Trigger multiple notifications quickly
4. **Auto-dismiss**: Verify toasts disappear after 4 seconds
5. **Manual dismiss**: Click the X button to close toast
6. **Mobile**: Test on mobile viewport

## Common Pitfalls

### ❌ Don't forget to remove JSX

```typescript
// Still shows old inline error even though you added toast
toast.error('Error occurred');

{error && <div>{error}</div>}  // ❌ Remove this!
```

### ❌ Don't mix patterns

```typescript
// Pick one approach - toast is preferred
setError('Error');  // ❌ Old pattern
toast.error('Error');  // ✅ New pattern
```

### ❌ Don't forget error in promise

```typescript
// Missing error handling
try {
  await someAsyncOperation();
  toast.success('Done!');
} catch (err) {
  // ❌ Forgot to show error toast!
}
```

## Rollout Plan

**Phase 1 - Auth Pages** (Highest Priority)
- [x] SignupPage
- [ ] LoginPage
- [ ] ForgotPasswordPage
- [ ] ResetPasswordPage

**Phase 2 - Core Features**
- [ ] CrawlsPage (most used)
- [ ] CrawlDetailPage

**Phase 3 - Secondary Pages**
- [ ] ProfilePage
- [ ] DashboardPage
- [ ] UsersPage

## Resources

- [Sonner Documentation](https://sonner.emilkowal.ski/)
- [Toast Pattern Best Practices](https://www.nngroup.com/articles/toast-notifications/)

---

**Last Updated**: 2025-12-26
**Status**: SignupPage migrated, 8 pages remaining