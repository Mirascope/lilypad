import { Hono } from 'hono';

import type { Environment } from '@/worker/environment';
import { initiateOAuth } from './oauth/initiate';
import {
  createGitHubProvider,
  handleOAuthCallback,
  createGoogleProvider,
} from './oauth';
import { handleLogout } from './logout';
import { handleMe } from './me';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';
import { authSessionMiddleware } from './middleware';

export const authRouter = new Hono<{
  Bindings: Environment;
  Variables: {
    db: PostgresJsDatabase;
  };
}>();

authRouter.get('/github', async (c) => {
  return await initiateOAuth(createGitHubProvider(c.env));
});

authRouter.get('/github/callback', async (c) => {
  return await handleOAuthCallback(c, createGitHubProvider(c.env));
});

authRouter.get('/google', async (c) => {
  return await initiateOAuth(createGoogleProvider(c.env));
});

authRouter.get('/google/callback', async (c) => {
  return await handleOAuthCallback(c, createGoogleProvider(c.env));
});

authRouter.post('/logout', async (c) => {
  return await handleLogout(c);
});

authRouter.get('/me', authSessionMiddleware, async (c) => {
  return await handleMe(c);
});
