# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## RULES

- Be clear, concise, and succinct ALWAYS
- Always ask questions first if the objective is not extremely clear
- Seek guidance and clarification from the user during development whenever necessary
- Favor smaller changes that are easier to review
- Whenever there are changes to the file structure, update `docs/file-structure.md` accordingly
- Ensure any changes requiring documentation have corresponding `docs/*` updates as well

## Development Commands

- `bun run dev` - Start development server on port 3000
- `bun run build` - Build for production (runs vite build && tsc)
- `bun test` - Run tests with bun
- `bun run deploy` - Deploy to Cloudflare Workers
- `bun run typecheck` - Run TypeScript type checking
- `bun run lint` - Run full linting suite (typecheck + eslint + prettier check)
- `bun run fix` - Auto-fix formatting and linting issues

## Architecture Overview

This is a full-stack React application deployed on Cloudflare Workers:

### Frontend (`src/`)

- **React 19** with **TanStack Router** for routing
- **Tailwind CSS v4** for styling with `@tailwindcss/vite` plugin
- **TanStack Query** for data fetching and caching
- Route files in `src/routes/` with auto-generated route tree in `routeTree.gen.ts`

### Backend (`worker/`)

- **Hono** framework running on Cloudflare Workers
- Two main route modules:
  - `worker/auth/` - Authentication routes (GitHub, Google OAuth)
  - `worker/api/` - API routes
- Security headers and CORS middleware configured in main worker
- Environment-specific CORS origins (development allows localhost)

### Database (`db/`)

- Database configuration and utilities

### Key Configuration

- **Path aliases**: `@/src`, `@/worker`, `@/db` configured in vite.config.ts
- **Cloudflare deployment**: wrangler.toml configured for v1.lilypad.mirascope.com
- **SPA routing**: Assets configured for single-page application handling
- **OAuth**: GitHub and Google OAuth configured with production URLs

### Development Setup

- Uses Bun as the package manager and runtime
- Vite for development server and build tooling
- ESLint + Prettier for code quality
- Vitest for testing with jsdom environment

## Important Notes

- Always run `bun run lint` before committing to ensure code quality
- The application uses React 19 features - ensure compatibility when adding new dependencies
- Worker routes are prefixed with `/api/*` and `/auth/*` in production
- Development environment allows localhost CORS, production is restricted to mirascope.com domains
