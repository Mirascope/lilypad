import { describe, expect, it, vi } from 'vitest';
import { authRouter, authSessionMiddleware } from './index';
import { authSessionMiddleware as middlewareAuthSessionMiddleware } from './middleware';
import { authRouter as routerAuthRouter } from './router';

vi.mock('./middleware', () => ({
  authSessionMiddleware: vi.fn(),
}));

vi.mock('./router', () => ({
  authRouter: {
    fetch: vi.fn(),
    routes: [],
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    route: vi.fn(),
  },
}));

describe('auth/index.ts exports', () => {
  it('should re-export authSessionMiddleware from ./middleware', () => {
    expect(authSessionMiddleware).toBeDefined();
    expect(authSessionMiddleware).toBe(middlewareAuthSessionMiddleware);
  });

  it('should re-export authRouter from ./router', () => {
    expect(authRouter).toBeDefined();
    expect(authRouter).toBe(routerAuthRouter);
  });

  it('should export the same middleware function reference', () => {
    expect(authSessionMiddleware).toStrictEqual(
      middlewareAuthSessionMiddleware
    );
    expect(vi.isMockFunction(authSessionMiddleware)).toBe(true);
  });

  it('should export the same router object reference', () => {
    expect(authRouter).toStrictEqual(routerAuthRouter);
    expect(authRouter.fetch).toBeDefined();
    expect(authRouter.route).toBeDefined();
  });
});
