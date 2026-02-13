# Admin Dashboard Navigation Refactor Guide

This guide details the steps to modify the frontend navigation structure, promoting "Research" and "Assistant" to top-level items.

## 1. Modify Sidebar (`components/app-sidebar.tsx`)

**Goal:** Move "Assistant" to the main navigation and add a "Research" item.

**File:** `admin-dashboard/components/app-sidebar.tsx`

**Changes:**

1. Import `IconSearch` from `@tabler/icons-react`.
2. Update `data.navMain`:
    * Add "Research" item (url: `/research`, icon: `IconSearch`).
    * Add "Assistant" item (url: `/assistant`, icon: `IconSparkles` or keep `IconFileWord` if preferred).
3. Remove "Assistant" from `data.documents`.

```tsx
// Example Snippet for data.navMain
{
  title: "Recherche",
  url: "/research",
  icon: IconSearch,
},
{
  title: "Assistant IA",
  url: "/assistant",
  icon: IconSparkles, // Import this!
},
```

## 2. Create Research Page (`app/research/page.tsx`)

**Goal:** Create a dedicated page for Web Research.

**File:** `admin-dashboard/app/research/page.tsx` (New File)

**Content:**
Copy the logic from the "Recherche" tab in `app/assistant/page.tsx`.

* Imports: `useSWR`, `fetchApi`, UI components (`Card`, `Input`, `Select`, etc.).
* State: `query`, `webQuery`, `webProvider`, `webLimit`.
* Data Fetching: `useSWR` for search and web research endpoints.
* JSX: Render the search interfaces (Guide Search & Advanced Web Research).

## 3. Simplify Assistant Page (`app/assistant/page.tsx`)

**Goal:** Remove tabs and focus solely on the AI Assistant (Khoj) interface.

**File:** `admin-dashboard/app/assistant/page.tsx`

**Changes:**

1. Remove `Tabs`, `TabsList`, `TabsContent`.
2. Remove all code related to "Recherche" (search state, web research state, SWR hooks for search).
3. Keep only `<AssistantProspectPanel />`.
4. Update imports to remove unused UI components.

## 4. Verification

1. Restart the dev server (`npm run dev` or `.\dev_cycle.ps1`).
2. Verify sidebar has "Recherche" and "Assistant IA".
3. Click "Recherche": Should show search inputs.
4. Click "Assistant IA": Should show the chat/action plan interface directly.
