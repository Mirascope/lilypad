import { describe, expect, it, vi } from 'vitest';
import { apiRouter } from './index';
import { apiRouter as routerApiRouter } from './router';

vi.mock('./router', () => ({
  apiRouter: {
    fetch: vi.fn(),
    routes: [],
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  },
}));

describe('api/index.ts exports', () => {
  it('should re-export apiRouter from ./router', () => {
    expect(apiRouter).toBeDefined();
    expect(apiRouter).toBe(routerApiRouter);
  });

  it('should export the same object reference as the router module', () => {
    expect(apiRouter).toStrictEqual(routerApiRouter);
  });

  it('should have all expected router methods', () => {
    expect(apiRouter.fetch).toBeDefined();
    expect(apiRouter.get).toBeDefined();
    expect(apiRouter.post).toBeDefined();
    expect(apiRouter.put).toBeDefined();
    expect(apiRouter.delete).toBeDefined();
    expect(apiRouter.patch).toBeDefined();
  });
});
