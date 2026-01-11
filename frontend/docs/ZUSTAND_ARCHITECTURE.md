# Zustand Architecture - The Golden Pattern

## 🏗️ The Three-Layer Architecture

| Layer        | Tool           | Responsibility                    |
|--------------|----------------|-----------------------------------|
| Auth state   | Supabase       | Who the user is                   |
| Server data  | DB + RLS       | What they're allowed to see       |
| Client state | Zustand        | How the UI feels                  |

### ⚠️ What Zustand Should NEVER Decide:

- ❌ Permissions
- ❌ Roles
- ❌ Access control
- ❌ Pricing tiers
- ❌ Ownership

**It can display them — but never enforce them.**

---

## 📏 Zustand Patterns That Scale Safely

### 1. Keep Zustand "Thin"

**Only store:**
- UI state
- Cached selections
- View preferences
- Optimistic updates

**❌ Don't store:**
```typescript
// BAD
interface AuthStore {
  user: User;           // ❌ Full user object
  token: string;        // ❌ Tokens
  secrets: string[];    // ❌ Secrets
  role: 'admin';        // ❌ Permissions as truth
  permissions: string[]; // ❌
}
```

**✅ Do this instead:**
```typescript
// GOOD
interface AuthStore {
  userId: string | null;      // ✅ Just the ID
  isAuthenticated: boolean;   // ✅ Boolean flag
}
```

**Those must always come from the server.**

---

### 2. Auth State: Mirror, Don't Own

**Let Supabase own auth. Zustand just mirrors it.**

```typescript
// Pattern:
supabase.auth.onAuthStateChange((event, session) => {
  useAuthStore.setState({
    userId: session?.user?.id ?? null,
    isAuthenticated: !!session,
  });
});
```

**Zustand becomes:**
> "A fast UI cache of auth state"

**Not:**
> "The source of truth"

---

### 3. Never Persist Sensitive Zustand Stores

**Big pitfall:** `persist()` middleware.

**❌ Bad:**
```typescript
const useAuthStore = create(
  persist(
    (set) => ({
      token: null,      // ❌ XSS = full compromise
      role: null,       // ❌ Users can edit localStorage
    }),
    { name: 'auth' }  // ❌ Writes to localStorage
  )
);
```

**This writes to:**
- localStorage
- sessionStorage
- IndexedDB

**Which means:**
- XSS = full compromise
- Shared computers leak data
- Users can edit it

**✅ Safe:**
Only persist:
```typescript
const useUIStore = create(
  persist(
    (set) => ({
      theme: 'light',           // ✅ Safe
      sidebarOpen: true,        // ✅ Safe
      lastViewedTab: 'pages',   // ✅ Safe
    }),
    { name: 'ui-preferences' }
  )
);
```

---

## 🛡️ Security Patterns with Zustand + Supabase

### 4. Treat Every Action as Hostile

Even if Zustand says:
```typescript
isAdmin: true
```

**Your backend must still check:**
- JWT claims
- RLS policies
- Server-side validation

**Zustand can be lied to. Postgres cannot (if RLS is correct).**

---

### 5. The "Read-Only Client" Mindset

Think of your frontend as:
> **A viewer of permissions, not an enforcer.**

**Flow:**
1. User clicks "Delete"
2. Zustand shows loading
3. API call happens
4. **DB decides** ← This is where security happens
5. Zustand reflects result

**Never:**
1. Zustand decides user can delete
2. API just executes

---

### 6. Use Zustand for Optimistic UX, Not Optimistic Security

**Optimistic updates are great — but:**

```typescript
// ✅ Good
const deleteCrawl = async (id: string) => {
  // Optimistic update
  useCrawlStore.getState().removeCrawl(id);

  try {
    await api.deleteCrawl(id);
  } catch (error) {
    // Rollback if server denies
    useCrawlStore.getState().addCrawl(crawl);
  }
};
```

**Because:**
- RLS might deny
- Role may have changed
- Session may be expired

---

## 🎯 Advanced Gems

### 7. Separate Stores by Trust Level

**Safe stores (persist OK):**
```typescript
// ✅ Can persist
const useUIStore = create(persist(...));
const usePreferenceStore = create(persist(...));
```

**Volatile stores (memory only):**
```typescript
// ❌ Never persist
const useAuthStore = create(...);        // No persist!
const useSessionStore = create(...);     // No persist!
const usePermissionsStore = create(...); // No persist!
```

**Rule:**
> **If it affects security, it dies on refresh.**

---

### 8. Never Derive Permissions in Zustand

**❌ Bad:**
```typescript
const useAuthStore = create((set) => ({
  user: null,
  canDelete: computed(() => user.role === 'admin'), // ❌
}));
```

**✅ Good:**
```typescript
// Frontend
const { data: permissions } = usePermissionsQuery();
const canDelete = permissions?.includes('delete');

// Backend MUST verify again
const { data, error } = await supabase
  .from('crawls')
  .delete()
  .eq('id', crawlId);
// RLS enforces the real permission
```

---

### 9. Don't Store Supabase Session in Zustand

**Supabase already manages:**
- Refresh tokens
- Expiry
- Rotation

**If you copy it into Zustand:**
- ❌ You'll desync
- ❌ You'll break refresh
- ❌ You'll cause ghost logins

**Instead:**
- ✅ Ask Supabase when you need auth
- ✅ Mirror only minimal UI state

```typescript
// ❌ Bad
const useAuthStore = create((set) => ({
  session: null,  // ❌ Don't duplicate Supabase's work
}));

// ✅ Good
const useAuthStore = create((set) => ({
  userId: null,           // ✅ Just the ID
  isAuthenticated: false, // ✅ Just a flag
}));
```

---

### 10. Zustand + Middleware = Hidden Risk

**Be careful with:**
- `devtools`
- `persist`
- `subscribeWithSelector`

**Security rule:**
> **Anything that serializes state must not touch auth data.**

---

## 🏆 A Battle-Tested Pattern

### Store Structure:
```typescript
// ✅ Persisted (safe)
const useUIStore = create(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      lastViewedTab: 'pages',
    }),
    { name: 'ui-preferences' }
  )
);

// ✅ In-memory only (volatile)
const useAuthMirrorStore = create((set) => ({
  userId: null,
  isAuthenticated: false,
}));

// ✅ In-memory only (volatile)
const useSelectionStore = create((set) => ({
  selectedCrawlId: null,
  selectedPageIds: [],
}));
```

### Data Fetching:
```typescript
// ✅ All real data via React Query / SWR
const { data: crawls } = useQuery('crawls', fetchCrawls);
const { data: permissions } = useQuery('permissions', fetchPermissions);
```

### Security:
- ✅ RLS on every table
- ✅ Service role only on server
- ✅ Edge functions for elevated ops

---

## 🚨 Common Traps (and How to Dodge Them)

| Trap | Why it hurts | Fix |
|------|--------------|-----|
| Storing roles in Zustand | Users can edit it | Fetch from server |
| Persisting auth store | Token leakage | Keep in memory |
| Trusting client flags | Easy to bypass | Enforce in DB |
| Syncing session manually | Breaks refresh | Let Supabase manage |
| Using Zustand as backend | No audit trail | Use RLS + logs |

---

## 🧠 Mental Model Upgrade

**Zustand is:**
> A UI performance engine

**Supabase + RLS is:**
> Your real backend

**If they ever disagree, Supabase wins.**

---

## 📦 Recommended Store Structure

```
frontend/src/store/
├── index.ts                 # Export all stores
├── uiStore.ts              # ✅ Persisted - theme, sidebar, etc.
├── authMirrorStore.ts      # ❌ Not persisted - mirrors Supabase
├── selectionStore.ts       # ❌ Not persisted - UI selections
└── types.ts                # Shared types
```

### Example: `authMirrorStore.ts`
```typescript
import { create } from 'zustand';
import { supabase } from '../lib/supabase';

interface AuthMirrorState {
  userId: string | null;
  isAuthenticated: boolean;
  email: string | null;
}

export const useAuthMirrorStore = create<AuthMirrorState>((set) => ({
  userId: null,
  isAuthenticated: false,
  email: null,
}));

// Initialize: Mirror Supabase auth state
supabase.auth.onAuthStateChange((event, session) => {
  useAuthMirrorStore.setState({
    userId: session?.user?.id ?? null,
    isAuthenticated: !!session,
    email: session?.user?.email ?? null,
  });
});
```

### Example: `uiStore.ts` (Safe to Persist)
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  lastViewedTab: string;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setLastViewedTab: (tab: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      lastViewedTab: 'pages',
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setLastViewedTab: (tab) => set({ lastViewedTab: tab }),
    }),
    {
      name: 'ui-preferences',
    }
  )
);
```

---

## ✅ Pre-Implementation Checklist

### Store Design:
- [ ] Separate stores by trust level
- [ ] Only persist safe UI preferences
- [ ] Never store tokens, secrets, or sessions
- [ ] Auth state mirrors Supabase, doesn't own it

### Security:
- [ ] All permissions verified by backend
- [ ] RLS policies enforce access control
- [ ] Zustand only for UI state, not security
- [ ] Optimistic updates have rollback logic

### Architecture:
- [ ] Zustand = UI cache
- [ ] Supabase = Auth source of truth
- [ ] RLS = Security enforcement
- [ ] React Query = Data fetching

---

## 🚀 Next Steps

1. Install Zustand: `npm install zustand`
2. Create store structure following the pattern above
3. Implement `authMirrorStore` (mirrors Supabase)
4. Implement `uiStore` (persisted preferences)
5. Refactor components to use stores
6. Test that security is enforced by backend, not Zustand

**Remember:** Zustand makes your UI fast and responsive. Supabase + RLS keeps your data secure. Never confuse the two.
