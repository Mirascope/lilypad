# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## RULES

- Be clear, concise, and succinct ALWAYS
- Always ask questions first if the objective is not extremely clear
- Seek guidance and clarification from the user during development whenever necessary
- Favor smaller changes that are easier to review
- Whenever there are changes to the file structure, update `docs/file-structure.md` accordingly
- Ensure any changes requiring documentation have corresponding `docs/*` updates as well
- Never create files unless absolutely necessary - always prefer editing existing files
- Never proactively create documentation files (\*.md) or README files unless explicitly requested

## Development Commands

### Core Development

- `bun run dev` - Start development server on port 3000
- `bun run build` - Build for production (runs vite build && tsc)
- `bun test` - Run tests with vitest (runs once and exits)
- `bun test:coverage` - Run tests with coverage report (runs once and exits)
- `bun test:watch` - Run tests in watch mode (continuous)
- `vitest run <pattern>` - Run specific test files matching pattern
- `bun run deploy` - Deploy to Cloudflare Workers (production)
- `bun run deploy:staging` - Deploy to staging environment

### Code Quality

- `bun run typecheck` - Run TypeScript type checking
- `bun run lint` - Run full linting suite (typecheck + eslint + prettier check)
- `bun run fix` - Auto-fix formatting and linting issues
- `bun run codespell` - Check for spelling errors across the codebase
- `bun run lint:ci` - CI-specific linting (includes codespell)

### Database Management

- `bun run db:start` - Start local PostgreSQL with Docker
- `bun run db:stop` - Stop local PostgreSQL
- `bun run db:generate` - Generate migrations from schema changes
- `bun run db:migrate` - Apply migrations to database
- `bun run db:studio` - Open Drizzle Studio for database inspection

## Architecture Overview

This is a full-stack React application with a serverless, cloud-native architecture that can be deployed on multiple cloud providers (Cloudflare primary, AWS alternative). See `docs/architecture/001-overview.md` for detailed architecture documentation.

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

- **Drizzle ORM** with PostgreSQL (local Docker) and Neon (production)
- Schema definitions in `db/schema/` with type-safe queries
- Database operations in `db/operations/`
- Migrations in `db/migrations/` with automatic generation
- ParadeDB with pg_search for full-text search capabilities

### Key Configuration

- **Path aliases**: `@/src`, `@/worker`, `@/db` configured in vite.config.ts
- **Cloudflare deployment**: wrangler.toml configured for v1.lilypad.mirascope.com
- **SPA routing**: Assets configured for single-page application handling
- **OAuth**: GitHub and Google OAuth configured with production URLs

### Development Setup

- Uses Bun as the package manager and runtime
- Vite for development server and build tooling
- ESLint + Prettier for code quality with pre-commit hooks (Husky + lint-staged)
- Vitest test runner with v8 coverage reporting (100% coverage requirement for db/)
- Docker Compose for local PostgreSQL development
- Environment variables configured in `.dev.vars` for local development
- Lint-staged runs full project typecheck and eslint on pre-commit

## Testing Strategy

- Test files are colocated with source files (\*.test.ts)
- Database tests use transaction rollback for isolation
- Test setup configured in `tests/setup.ts`
- Run single test file: `vitest path/to/file.test.ts`
- Generate coverage report: `bun test:coverage`

## Environment Configuration

Required environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth
- `SITE_URL` - Application URL (e.g., https://v1.lilypad.mirascope.com)
- `ENVIRONMENT` - development/staging/production
- `TEST_DATABASE_URL` - Test database connection string (for vitest tests)

## Infrastructure & Deployment

- **Production**: v1.lilypad.mirascope.com (Cloudflare Workers)
- **Staging**: staging.lilypad.mirascope.com (auto-deploys on PR merge)
- **Database**: Neon PostgreSQL with ParadeDB pg_search extensions (production), local Docker (development)
- **Storage**: Cloudflare R2 for blob storage
- **Caching**: Cloudflare KV Store
- **Background Jobs**: Cloudflare Queues
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Preview Deployments**: Automatic for PRs with Neon database branching

## Important Notes

- Always run `bun run lint` before committing to ensure code quality
- The application uses React 19 features - ensure compatibility when adding new dependencies
- Worker routes are prefixed with `/api/*` and `/auth/*` in production
- Development environment allows localhost CORS, production is restricted to mirascope.com domains
- Database migrations must be generated (`db:generate`) before running `db:migrate`
- Cloudflare bindings (KV, R2, Queues) are configured in `wrangler.toml`
- Pre-commit hooks automatically run linting and formatting via Husky
- The database directory (`db/`) requires 100% test coverage
- PR preview deployments create separate Neon database branches automatically
