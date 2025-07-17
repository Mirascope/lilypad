# File Structure

This document outlines the codebase structure for the Lilypad application, a full-stack React app deployed on Cloudflare Workers.

## Overview

```text
lilypad/
├── src/                    # Frontend React application
├── worker/                 # Backend Cloudflare Workers
├── db/                     # Database configuration
├── docs/                   # Documentation
├── public/                 # Static assets
└── [config files]          # Build and deployment configuration
```

## Frontend (`src/`)

The React single-page application that provides the user interface and client-side functionality.

```text
src/
├── api/                   # API client utilities
│   ├── client.ts            # HTTP client configuration
│   └── index.ts             # API exports
├── lib/                   # Shared utilities
│   └── utils.ts             # Common helper functions
├── routes/                # TanStack Router pages
│   ├── __root.tsx           # Root layout component
│   └── index.tsx            # Home page
├── main.tsx               # React app entry point
├── reportWebVitals.ts     # Performance monitoring
└── routeTree.gen.ts       # Auto-generated route tree
```

**Tooling Choices**:

- **React 19**: Modern React features and performance improvements
- **TanStack Router**: File-based routing with type-safe navigation
- **TanStack Query**: Server state management with caching and synchronization
- **Tailwind CSS v4**: Utility-first CSS with Vite plugin integration

## Backend (`worker/`)

The serverless backend running on Cloudflare Workers that handles API requests and authentication.

```text
worker/
├── api/                  # API handlers
│   ├── routes/             # API routes
│   │   └── index.ts          # API route module exports
│   └── index.ts            # API module exports
├── auth/                 # Auth handlers
│   ├── routes/             # Auth routes
│   │   └── index.ts          # Auth route module exports
│   └── index.ts            # Auth module exports
├── environment.ts        # Environment configuration
└── index.ts              # Main worker entry point
```

**Tooling Choices**:

- **Hono**: Lightweight web framework with excellent TypeScript support
- **Cloudflare Workers**: Global edge deployment with automatic scaling
- **OAuth Integration**: GitHub and Google authentication with production URLs

## Database (`db/`)

Shared database utilities, schema definitions, and operations used by both frontend and backend.

```text
db/
├── index.ts                         # Main database exports
├── middleware.ts                    # Hono middleware for database connections
├── utils.ts                         # Database connection utilities
├── migrations/                      # Database migrations
│   ├── ...
├── operations/                      # Database operations
│   ├── index.ts                       # Operations exports
│   └── users.ts                       # User-related operations
└── schema/                          # Database schema definitions
    ├── index.ts                       # Schema exports and types
    ├── users.ts                       # User table schema
    ├── organizations.ts               # Organization table schema
    ├── organization-memberships.ts    # Membership table schema
    └── user-consents.ts               # User consent table schema
```

**Tooling Choices**:

- **Drizzle ORM**: Type-safe SQL toolkit with PostgreSQL support
- **postgres-js**: PostgreSQL client for Node.js
- **ParadeDB with `pg_search`**: Enhanced PostgreSQL with full-text search capabilities
- **Neon**: Serverless PostgreSQL hosting for production
- **Schema-first design**: Organized table definitions with proper foreign key relationships
- **Migration system**: Version-controlled database schema changes

## Static Assets (`public/`)

Static files served directly by Cloudflare Workers without processing.

```text
public/
├── fonts/                 # Custom fonts
├── icons/                 # App icons and favicons
├── manifest.json          # PWA manifest
└── robots.txt             # SEO configuration
```

**Tooling Choices**:

- **Cloudflare Workers**: Direct static file serving with global CDN
- **PWA Support**: Progressive web app configuration with manifest.json

## Configuration Files

- **`wrangler.toml`**: Cloudflare Workers deployment configuration
- **`vite.config.ts`**: Build tool configuration with path aliases (`@/src`, `@/worker`, `@/db`)
- **`tsconfig.json`**: TypeScript configuration
- **`eslint.config.ts`**: Code quality rules
- **`package.json`**: Dependencies and scripts using Bun runtime

## Key Design Decisions

1. **Separation of Concerns**: Frontend (`src/`) and backend (`worker/`) are clearly separated with shared database utilities (`db/`)

2. **Path Aliases**: `@/src`, `@/worker`, `@/db` configured in Vite for clean imports

3. **Route Organization**:
   - Frontend uses file-based routing with TanStack Router
   - Backend separates API and auth concerns into dedicated modules

4. **Asset Handling**: Static assets in `public/` with SPA routing configured in `wrangler.toml`

5. **Environment-Specific Configuration**: Production OAuth URLs and CORS origins configured for `lilypad.mirascope.com`

This structure enables easy development with clear boundaries between frontend, backend, and shared utilities while maintaining deployment simplicity on Cloudflare Workers.
