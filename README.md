# Lilypad

Under active development...

## ⚠️ License & Usage

This is proprietary software - while the source code is publicly viewable, it is NOT open source.

What you CAN do:

- ✅ View and study the source code for evaluation
- ✅ Use for non-commercial development and testing
- ✅ Provide feedback and suggestions

What you CANNOT do:

- ❌ Use in production environments
- ❌ Self-host or deploy without a license
- ❌ Redistribute or share copies
- ❌ Create competing products or services
- ❌ Modify and redistribute derivative works

### Need to use Lilypad in production?

Commercial use, production deployment, and self-hosting require an Enterprise License.

📧 Get a license: support@mirascope.com

Full license terms: See [LICENSE](./LICENSE) file

By using this software, you agree to be bound by the license terms.

## Development Commands

### Core Development

- `bun run dev` - Start development server on port 3000
- `bun run build` - Build for production (runs vite build && tsc)
- `bun test` - Run tests with vitest (runs once and exits)
- `bun test:coverage` - Run tests with coverage report (runs once and exits)
- `bun test:watch` - Run tests in watch mode (continuous)
- `bun test <pattern>` - Run specific test files matching pattern
- `bun run deploy` - Deploy to Cloudflare Workers (production)
- `bun run deploy:staging` - Deploy to staging environment

### Code Quality

- `bun run typecheck` - Run TypeScript type checking
- `bun run lint` - Run full linting suite (typecheck + eslint + prettier check)
- `bun run fix` - Auto-fix formatting and linting issues

### Database Management

- `bun run db:start` - Start local PostgreSQL with Docker
- `bun run db:stop` - Stop local PostgreSQL
- `bun run db:generate` - Generate migrations from schema changes
- `bun run db:migrate` - Apply migrations to database
- `bun run db:studio` - Open Drizzle Studio for database inspection

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
- ESLint + Prettier for code quality
- Vitest test runner with v8 coverage reporting
- Docker Compose for local PostgreSQL development
- Environment variables configured in `.dev.vars` for local development

## Testing Strategy

- Test files are colocated with source files (\*.test.ts)
- Database tests use transaction rollback for isolation
- Test setup configured in `tests/db/setup.ts`
- Run single test file: `bun test path/to/file.test.ts`
- Generate coverage report: `bun test:coverage`

## Environment Configuration

To run the system locally, you'll need to configure your `.dev.vars` and `.env.local` environments. You can see `.example.dev.vars` and `.example.env.local` for examples of the variables required.

Required environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth
- `SITE_URL` - Application URL (e.g., https://v1.lilypad.mirascope.com)
- `ENVIRONMENT` - development/staging/production
- `TEST_DATABASE_URL` - Test database connection string (for vitest tests)

Example configuration:

```bash
ENVIRONMENT=development
SITE_URL=http://localhost:3000
DATABASE_URL=postgres://postgres:postgres@localhost:5432/lilypad_dev
GITHUB_CLIENT_ID=...        # GitHub OAuth Client ID
GITHUB_CLIENT_SECRET=...    # GitHub OAuth Client Secret
GITHUB_CALLBACK_URL=http://localhost:3000/auth/github/callback
GOOGLE_CLIENT_ID=...        # Google OAuth Client ID
GOOGLE_CLIENT_SECRET=...    # Google OAuth Client Secret
GOOGLE_CALLBACK_URL=http://localhost:3000/auth/google/callback
```

For Google and GitHub OAuth, ask William for development credentials. You must configure at least one OAuth provider. The ones you set will appear on the login screen as options for signing in.

## Infrastructure & Deployment

- **Production**: v1.lilypad.mirascope.com (Cloudflare Workers)
- **Staging**: staging.lilypad.mirascope.com
- **Database**: Neon PostgreSQL (production), local Docker (development)
- **Storage**: Generic abstraction supporting Cloudflare R2, AWS S3, and other blob storage providers
- **Caching**: Generic abstraction supporting Cloudflare KV Store, Redis, and other caching solutions
- **Background Jobs**: Cloudflare Queues
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Preview Deployments**: Automatic for pull requests

## Important Notes

- Always run `bun run lint` before committing to ensure code quality
- The application uses React 19 features - ensure compatibility when adding new dependencies
- Worker routes are prefixed with `/api/*` and `/auth/*` in production
- Development environment allows localhost CORS, production is restricted to mirascope.com domains
- Database migrations must be generated (`db:generate`) before running `db:migrate`
- Cloudflare bindings (KV, R2, Queues) are configured in `wrangler.toml`
