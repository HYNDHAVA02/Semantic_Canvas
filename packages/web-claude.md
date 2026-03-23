# packages/web

Next.js 15 dashboard. Secondary interface — AI agents via MCP are the primary consumers. This is a simple CRUD UI for browsing, searching, and editing the knowledge base.

Deployed on Vercel. Calls FastAPI REST endpoints.

## Structure

```
app/
  layout.tsx               # Root layout, providers (QueryClient, Auth)
  page.tsx                 # Landing / project list
  login/page.tsx           # Firebase Auth login
  projects/
    [projectId]/
      layout.tsx           # Project layout with sidebar nav
      page.tsx             # Project overview (entity counts, recent activity)
      entities/page.tsx    # Entity list with filters
      entities/[id]/page.tsx
      relationships/page.tsx
      decisions/page.tsx
      conventions/page.tsx
      activity/page.tsx
      search/page.tsx      # Global search
      settings/page.tsx    # Project settings, MCP connection info, PAT management
components/
  ui/                      # Shared UI primitives (shadcn/ui style)
  entities/                # Entity-specific components
  layout/                  # Sidebar, header, navigation
lib/
  api.ts                   # API client (fetch wrapper, auth headers)
  auth.ts                  # Firebase Auth context + hooks
  types.ts                 # Shared TypeScript types matching API DTOs
```

## Patterns

- App Router with server components where possible
- Client components only for interactive elements (search, forms, filters)
- React Query for all API calls (no raw fetch in components)
- Firebase Auth: `onAuthStateChanged` → store JWT → send in `Authorization` header
- API base URL from `NEXT_PUBLIC_API_URL` env var
- Tailwind for all styling, no CSS modules
- No state management library — React Query + URL params + React state covers everything

## Commands

```bash
pnpm dev          # start dev server
pnpm build        # production build
pnpm test         # run tests
pnpm lint         # eslint
pnpm typecheck    # tsc --noEmit
```

## Environment Variables

```
NEXT_PUBLIC_API_URL=http://localhost:8000    # FastAPI server
NEXT_PUBLIC_FIREBASE_CONFIG=<json-string>   # Firebase client config
```
