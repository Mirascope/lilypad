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
├── docker/                 # Docker development environment
├── scripts/                # Build and utility scripts
├── .github/                # GitHub Actions workflows
└── [config files]          # Build and deployment configuration
```

## Frontend (`src/`)

The React single-page application that provides the user interface and client-side functionality.

```text
src/
├── api/                   # API client utilities
│   ├── auth/                # Authentication API endpoints
│   │   ├── index.ts           # Auth API exports
│   │   ├── logout.ts          # Logout endpoint
│   │   └── status.ts          # Auth status endpoint
│   ├── client.ts            # HTTP client configuration
│   └── index.ts             # API exports
├── components/            # React components
│   ├── ui/                  # ShadCN UI component library
│   │   ├── button.tsx         # ShadCN Button component
│   │   └── card.tsx           # ShadCN Card component
│   ├── home-page.tsx        # Home page component
│   ├── login-page.tsx       # Login page component
│   └── protected.tsx        # Protected route wrapper
├── lib/                   # Shared utilities
│   └── utils.ts             # Common helper functions (includes ShadCN utils)
├── routes/                # TanStack Router pages
│   ├── __root.tsx           # Root layout component
│   └── index.tsx            # Home page route
├── styles/                # CSS and styling
│   └── globals.css          # Global styles with Tailwind
├── auth.tsx               # Authentication utilities
├── main.tsx               # React app entry point
├── reportWebVitals.ts     # Performance monitoring
└── routeTree.gen.ts       # Auto-generated route tree
```

**Tooling Choices**:

- **React 19**: Modern React features and performance improvements
- **TanStack Router**: File-based routing with type-safe navigation
- **TanStack Query**: Server state management with caching and synchronization
- **Tailwind CSS v4**: Utility-first CSS with Vite plugin integration
- **ShadCN**: Component library built on Tailwind CSS and Radix UI primitives

## Backend (`worker/`)

The serverless backend running on Cloudflare Workers that handles API requests and authentication.

```text
worker/
├── api/                  # API handlers
│   ├── schemas/            # Shared API schemas
│   │   └── common.ts         # Common response schemas
│   ├── index.ts            # API route handlers
│   └── router.ts           # API router with OpenAPI documentation
├── auth/                 # Authentication handlers
│   ├── middleware/         # Auth middleware
│   │   ├── index.ts          # Middleware exports
│   │   └── session.ts        # Session middleware
│   ├── oauth/              # OAuth providers
│   │   ├── providers/        # OAuth provider implementations
│   │   │   ├── github.ts       # GitHub OAuth
│   │   │   ├── google.ts       # Google OAuth
│   │   │   └── index.ts        # Provider exports
│   │   ├── callback.ts       # OAuth callback handler
│   │   ├── index.ts          # OAuth exports
│   │   ├── initiate.ts       # OAuth initiation
│   │   ├── proxy-callback.ts # OAuth proxy callback
│   │   └── types.ts          # OAuth type definitions
│   ├── routes.ts           # OpenAPI route definitions
│   ├── schemas.ts          # Zod schemas for validation
│   ├── index.ts            # Auth route handlers
│   ├── router.ts           # Auth router with OpenAPI documentation
│   ├── router.test.ts      # Consolidated router, schema, and integration tests
│   └── utils.ts            # Auth utilities
├── tests/
│   └── integration.test.ts # Integration tests
├── environment.ts        # Environment configuration
└── index.ts              # Main worker entry point
```

**Tooling Choices**:

- **Hono**: Lightweight web framework with excellent TypeScript support
- **Cloudflare Workers**: Global edge deployment with automatic scaling
- **OAuth Integration**: GitHub and Google authentication with production URLs
- **OpenAPI with Zod**: Type-safe API documentation using @hono/zod-openapi
- **Swagger UI**: Interactive API documentation at `/docs`

## Database (`db/`)

Shared database utilities, schema definitions, and operations used by both frontend and backend.

```text
db/
├── index.ts                         # Main database exports
├── middleware.ts                    # Hono middleware for database connections
├── utils.ts                         # Database connection utilities
├── migrations/                      # Database migrations
│   ├── 0000_users_organizations.sql   # Initial user/org tables
│   ├── 0001_auth_sessions.sql         # Authentication sessions
│   └── meta/                          # Migration metadata
│       ├── 0000_snapshot.json           # Migration snapshots
│       ├── 0001_snapshot.json
│       └── _journal.json                # Migration journal
├── operations/                      # Database operations
│   ├── index.ts                       # Operations exports
│   ├── sessions.ts                    # Session operations
│   ├── sessions.test.ts               # Session operations tests
│   ├── users.ts                       # User-related operations
│   └── users.test.ts                  # User operations tests
└── schema/                          # Database schema definitions
    ├── index.ts                       # Schema exports and types
    ├── users.ts                       # User table schema
    ├── organizations.ts               # Organization table schema
    ├── organization-memberships.ts    # Membership table schema
    ├── sessions.ts                    # Session table schema
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

## Development Environment (`docker/`)

Local development environment with containerized services.

```text
docker/
├── compose.yml             # Docker Compose configuration
└── data/                   # PostgreSQL data directory (generated)
```

**Tooling Choices**:

- **Docker Compose**: Local PostgreSQL development environment
- **ParadeDB**: Enhanced PostgreSQL with full-text search capabilities for local development

## Build Scripts (`scripts/`)

Utility scripts for build and development processes.

```text
scripts/
└── lint-staged.ts          # Pre-commit linting configuration
```

## Tests (`tests/`)

Global test configuration and setup files.

```text
tests/
└── setup.ts                # Global test setup and configuration
```

## GitHub Actions (`.github/`)

CI/CD workflows and GitHub configuration.

```text
.github/
├── workflows/              # GitHub Actions workflows
│   ├── cleanup-preview.yml   # Preview cleanup workflow
│   ├── deploy.yml            # Production deployment
│   ├── lint.yml              # Code quality checks
│   ├── preview-deploy.yml    # Preview deployments
│   └── test.yml              # Test execution workflow
└── ISSUE_TEMPLATE/         # Issue templates
    ├── bug-report.yml         # Bug report template
    ├── feature-request.yml    # Feature request template
    ├── question.yml           # Question template
    └── config.yml             # Issue template configuration
```

**Tooling Choices**:

- **GitHub Actions**: Automated CI/CD with Cloudflare Workers deployment
- **Preview Deployments**: Automated staging environments for pull requests
- **Code Quality**: Automated linting and type checking on all PRs

## Configuration Files

- **`wrangler.toml`**: Cloudflare Workers deployment configuration
- **`vite.config.ts`**: Build tool configuration with path alias (`@` to project root)
- **`tsconfig.json`**: TypeScript configuration
- **`eslint.config.ts`**: Code quality rules
- **`drizzle.config.ts`**: Database ORM configuration
- **`components.json`**: ShadCN component configuration
- **`package.json`**: Dependencies and scripts using Bun runtime
- **`.prettierrc`**: Code formatting configuration
- **`.husky/pre-commit`**: Git pre-commit hooks

## Key Design Decisions

1. **Separation of Concerns**: Frontend (`src/`) and backend (`worker/`) are clearly separated with shared database utilities (`db/`)

2. **Path Aliases**: `@` configured in Vite to point to project root, enabling clean imports like `@/src`, `@/worker`, `@/db`

3. **Route Organization**:
   - Frontend uses file-based routing with TanStack Router
   - Backend separates API and auth concerns into dedicated modules

4. **Asset Handling**: Static assets in `public/` with SPA routing configured in `wrangler.toml`

5. **Environment-Specific Configuration**: Production OAuth URLs and CORS origins configured for `lilypad.mirascope.com`

This structure enables easy development with clear boundaries between frontend, backend, and shared utilities while maintaining deployment simplicity on Cloudflare Workers.
