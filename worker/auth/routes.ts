import { createRoute } from '@hono/zod-openapi';
import {
  LogoutErrorResponseSchema,
  LogoutSuccessResponseSchema,
  MeErrorResponseSchema,
  MeSuccessResponseSchema,
  OAuthCallbackQuerySchema,
} from './schemas';

// /auth/me route
export const meRoute = createRoute({
  method: 'get',
  path: '/me',
  tags: ['Authentication'],
  summary: 'Get current user',
  description:
    'Returns information about the currently authenticated user. Requires a valid session cookie.',
  security: [{ cookieAuth: [] }],
  responses: {
    200: {
      description: 'Successfully retrieved user information',
      content: {
        'application/json': {
          schema: MeSuccessResponseSchema,
        },
      },
    },
    401: {
      description: 'Authentication required or invalid session',
      content: {
        'application/json': {
          schema: MeErrorResponseSchema,
        },
      },
    },
    500: {
      description: 'Internal server error',
      content: {
        'application/json': {
          schema: MeErrorResponseSchema,
        },
      },
    },
  },
});

// /auth/logout route
export const logoutRoute = createRoute({
  method: 'post',
  path: '/logout',
  tags: ['Authentication'],
  summary: 'Logout user',
  description:
    'Logs out the current authenticated user by clearing their session cookie.',
  responses: {
    200: {
      description: 'Successfully logged out',
      headers: {
        'Set-Cookie': {
          description: 'Clears the session cookie',
          schema: { type: 'string' },
        },
      },
      content: {
        'application/json': {
          schema: LogoutSuccessResponseSchema,
        },
      },
    },
    400: {
      description: 'No active session found',
      content: {
        'application/json': {
          schema: LogoutErrorResponseSchema,
        },
      },
    },
    500: {
      description: 'Logout failed due to server error',
      content: {
        'application/json': {
          schema: LogoutErrorResponseSchema,
        },
      },
    },
  },
});

// OAuth initiation routes (documentation only)
export const githubOAuthRoute = createRoute({
  method: 'get',
  path: '/github',
  tags: ['Authentication'],
  summary: 'Initiate GitHub OAuth',
  description:
    'Redirects the user to GitHub OAuth authorization page. Sets an oauth_state cookie for CSRF protection.',
  responses: {
    302: {
      description: 'Redirect to GitHub OAuth authorization page',
      headers: {
        Location: {
          description: 'GitHub OAuth authorization URL',
          schema: { type: 'string' },
        },
        'Set-Cookie': {
          description: 'OAuth state cookie for CSRF protection',
          schema: { type: 'string' },
        },
      },
    },
  },
});

export const googleOAuthRoute = createRoute({
  method: 'get',
  path: '/google',
  tags: ['Authentication'],
  summary: 'Initiate Google OAuth',
  description:
    'Redirects the user to Google OAuth authorization page. Sets an oauth_state cookie for CSRF protection.',
  responses: {
    302: {
      description: 'Redirect to Google OAuth authorization page',
      headers: {
        Location: {
          description: 'Google OAuth authorization URL',
          schema: { type: 'string' },
        },
        'Set-Cookie': {
          description: 'OAuth state cookie for CSRF protection',
          schema: { type: 'string' },
        },
      },
    },
  },
});

// OAuth callback routes
export const githubCallbackRoute = createRoute({
  method: 'get',
  path: '/github/callback',
  tags: ['Authentication'],
  summary: 'GitHub OAuth callback',
  description:
    'Handles the OAuth callback from GitHub. Validates the state parameter and exchanges the code for user information.',
  request: {
    query: OAuthCallbackQuerySchema,
  },
  responses: {
    302: {
      description: 'Redirect to application with authentication result',
      headers: {
        Location: {
          description: 'Application URL with success/error parameters',
          schema: { type: 'string' },
        },
        'Set-Cookie': {
          description: 'Session cookie on successful authentication',
          schema: { type: 'string' },
        },
      },
    },
  },
});

export const googleCallbackRoute = createRoute({
  method: 'get',
  path: '/google/callback',
  tags: ['Authentication'],
  summary: 'Google OAuth callback',
  description:
    'Handles the OAuth callback from Google. Validates the state parameter and exchanges the code for user information.',
  request: {
    query: OAuthCallbackQuerySchema,
  },
  responses: {
    302: {
      description: 'Redirect to application with authentication result',
      headers: {
        Location: {
          description: 'Application URL with success/error parameters',
          schema: { type: 'string' },
        },
        'Set-Cookie': {
          description: 'Session cookie on successful authentication',
          schema: { type: 'string' },
        },
      },
    },
  },
});

// Proxy callback routes (for development)
export const githubProxyCallbackRoute = createRoute({
  method: 'get',
  path: '/github/proxy-callback',
  tags: ['Authentication'],
  summary: 'GitHub OAuth proxy callback',
  description:
    'Proxy endpoint for development/preview environments. Forwards OAuth callback to the preview environment.',
  request: {
    query: OAuthCallbackQuerySchema,
  },
  responses: {
    302: {
      description: 'Redirect to preview environment callback URL',
      headers: {
        Location: {
          description: 'Preview environment callback URL with query parameters',
          schema: { type: 'string' },
        },
      },
    },
  },
});

export const googleProxyCallbackRoute = createRoute({
  method: 'get',
  path: '/google/proxy-callback',
  tags: ['Authentication'],
  summary: 'Google OAuth proxy callback',
  description:
    'Proxy endpoint for development/preview environments. Forwards OAuth callback to the preview environment.',
  request: {
    query: OAuthCallbackQuerySchema,
  },
  responses: {
    302: {
      description: 'Redirect to preview environment callback URL',
      headers: {
        Location: {
          description: 'Preview environment callback URL with query parameters',
          schema: { type: 'string' },
        },
      },
    },
  },
});
