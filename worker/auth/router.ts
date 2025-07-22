import { Hono } from 'hono';

import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import { handleLogout } from './logout';
import { handleMe } from './me';
import { authSessionMiddleware } from './middleware';
import {
  createGitHubProvider,
  createGoogleProvider,
  handleOAuthCallback,
  handleOAuthProxyCallback,
} from './oauth';
import { initiateOAuth } from './oauth/initiate';

export const authRouter = new Hono<{
  Bindings: Environment;
  Variables: {
    db: Database;
  };
}>();

authRouter.get('/github', async (c) => {
  const currentUrl = new URL(c.req.url).origin;
  return await initiateOAuth(createGitHubProvider(c.env), currentUrl);
});

authRouter.get('/github/callback', async (c) => {
  return await handleOAuthCallback(c, createGitHubProvider(c.env));
});

authRouter.get('/github/proxy-callback', async (c) => {
  return await handleOAuthProxyCallback(c, 'github');
});

authRouter.get('/google', async (c) => {
  const currentUrl = new URL(c.req.url).origin;
  return await initiateOAuth(createGoogleProvider(c.env), currentUrl);
});

authRouter.get('/google/callback', async (c) => {
  return await handleOAuthCallback(c, createGoogleProvider(c.env));
});

authRouter.get('/google/proxy-callback', async (c) => {
  return await handleOAuthProxyCallback(c, 'google');
});

authRouter.post('/logout', async (c) => {
  return await handleLogout(c);
});

authRouter.get('/me', authSessionMiddleware, async (c) => {
  return await handleMe(c);
});
