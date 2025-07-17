import { createMiddleware } from 'hono/factory';
import { createDbConnection } from './utils';

export const dbMiddleware = createMiddleware(async (c, next) => {
  const databaseUrl = c.env?.DATABASE_URL || process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error('DATABASE_URL is required');
  }

  c.set('db', createDbConnection(databaseUrl));
  await next();
});
