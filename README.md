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

- `bun run dev` - Start development server on port 3000
- `bun run build` - Build for production (runs vite build && tsc)
- `bun test` - Run tests with vitest
- `bun test:coverage` - Run tests with coverage report
- `bun test:watch` - Run tests in watch mode
- `bun run deploy` - Deploy to Cloudflare Workers
- `bun run typecheck` - Run TypeScript type checking
- `bun run lint` - Run full linting suite (typecheck + eslint + prettier check)
- `bun run fix` - Auto-fix formatting and linting issues

### Database Commands

- `bun run db:start` - Start PostgreSQL database using Docker Compose
- `bun run db:stop` - Stop PostgreSQL database
- `bun run db:generate` - Generate database migration files from schema changes
- `bun run db:migrate` - Apply database migrations
- `bun run db:studio` - Open Drizzle Studio for database management

## Development Environment

To run the system locally, you'll need to configure your `.dev.vars` and `.env.local` environments. You can see `.example.dev.vars` and `.example.env.local` for examples of the variables required. For reference, you need:

```bash
ENVIRONMENT=development
SITE_URL=http://localhost:3000
DATABASE_URL=postgres://postgres:postgres@localhost:5432/lilypad_dev
GITHUB_CLIENT_ID=...        # Google Cloud OAuth Client ID
GITHUB_CLIENT_SECRET=...    # Google Cloud OAuth Client Secret
GITHUB_CALLBACK_URL=http://localhost:3000/auth/github/callback
GOOGLE_CLIENT_ID=...        # GitHub OAuth Client ID
GOOGLE_CLIENT_SECRET=...    # GitHub OAuth Client Secret
GOOGLE_CALLBACK_URL=http://localhost:3000/auth/google/callback
```

For Google and GitHub OAuth, ask William for development credentials. You must configure at least one OAuth provider. The ones you set will appear on the login screen as options for signing in.
