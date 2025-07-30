import type { User } from '@/db/schema';
import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import { OpenAPIHono } from '@hono/zod-openapi';
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
import {
  githubCallbackRoute,
  githubOAuthRoute,
  githubProxyCallbackRoute,
  googleCallbackRoute,
  googleOAuthRoute,
  googleProxyCallbackRoute,
  logoutRoute,
  meRoute,
} from './routes';

export const authRouter = new OpenAPIHono<{
  Bindings: Environment;
  Variables: {
    db: Database;
    user: User;
  };
}>();

// /auth/me - with Zod validation
authRouter.openapi(meRoute, authSessionMiddleware as any, handleMe as any);

// /auth/logout - with Zod validation
authRouter.openapi(logoutRoute, handleLogout as any);

// OAuth routes - documentation only, no Zod validation needed
authRouter.openapi(githubOAuthRoute, async (c: any) => {
  const currentUrl = new URL(c.req.url).origin;
  return await initiateOAuth(createGitHubProvider(c.env), currentUrl);
});

authRouter.openapi(googleOAuthRoute, async (c: any) => {
  const currentUrl = new URL(c.req.url).origin;
  return await initiateOAuth(createGoogleProvider(c.env), currentUrl);
});

authRouter.openapi(githubCallbackRoute, async (c: any) => {
  return await handleOAuthCallback(c, createGitHubProvider(c.env));
});

authRouter.openapi(googleCallbackRoute, async (c: any) => {
  return await handleOAuthCallback(c, createGoogleProvider(c.env));
});

authRouter.openapi(githubProxyCallbackRoute, async (c: any) => {
  return await handleOAuthProxyCallback(c, 'github');
});

authRouter.openapi(googleProxyCallbackRoute, async (c: any) => {
  return await handleOAuthProxyCallback(c, 'google');
});
