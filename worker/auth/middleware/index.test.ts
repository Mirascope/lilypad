import { describe, expect, it, vi } from 'vitest';
import { authSessionMiddleware } from './index';
import { authSessionMiddleware as sessionAuthSessionMiddleware } from './session';

vi.mock('./session', () => ({
  authSessionMiddleware: vi.fn(),
}));

describe('auth/middleware/index.ts exports', () => {
  it('should re-export authSessionMiddleware from ./session', () => {
    expect(authSessionMiddleware).toBeDefined();
    expect(authSessionMiddleware).toBe(sessionAuthSessionMiddleware);
  });

  it('should export the same function reference as the session module', () => {
    expect(authSessionMiddleware).toStrictEqual(sessionAuthSessionMiddleware);
  });

  it('should be a mock function (from the mocked session module)', () => {
    expect(vi.isMockFunction(authSessionMiddleware)).toBe(true);
  });

  it('should be callable', () => {
    const mockContext = { env: {}, req: {} };
    const mockNext = vi.fn();

    authSessionMiddleware(mockContext as any, mockNext);

    expect(authSessionMiddleware).toHaveBeenCalledWith(mockContext, mockNext);
  });
});
