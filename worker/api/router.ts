import type { User } from '@/db/schema';
import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import { OpenAPIHono } from '@hono/zod-openapi';

export const apiRouter = new OpenAPIHono<{
  Bindings: Environment;
  Variables: {
    db: Database;
    user?: User;
  };
}>();
