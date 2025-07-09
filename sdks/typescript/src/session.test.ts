import { describe, it, expect } from 'vitest';
import {
  session,
  sessionAsync,
  getCurrentSession,
  withSession,
  withSessionAsync,
  generateSessionId,
  type Session,
} from './session';

describe('Session Management', () => {
  describe('generateSessionId', () => {
    it('should generate a 32-character hexadecimal ID', () => {
      const id = generateSessionId();
      expect(id).toMatch(/^[a-f0-9]{32}$/);
    });

    it('should generate unique IDs', () => {
      const id1 = generateSessionId();
      const id2 = generateSessionId();
      expect(id1).not.toBe(id2);
    });
  });

  describe('session', () => {
    it('should create a session with auto-generated ID', () => {
      const sess = session();
      expect(sess.id).toBeTruthy();
      expect(sess.id).toMatch(/^[a-f0-9]{32}$/);
    });

    it('should create a session with specific ID', () => {
      const customId = 'custom-session-123';
      const sess = session(customId);
      expect(sess.id).toBe(customId);
    });

    it('should create a session with null ID', () => {
      const sess = session(null);
      expect(sess.id).toBe(null);
    });

    it('should run callback within session context', () => {
      let capturedSession: Session | null = null;
      const result = session(() => {
        capturedSession = getCurrentSession();
        return 'test-result';
      });

      expect(result).toBe('test-result');
      expect(capturedSession).toBeTruthy();
      expect(capturedSession!.id).toMatch(/^[a-f0-9]{32}$/);
    });

    it('should run callback with custom session ID', () => {
      const customId = 'custom-id-456';
      let capturedSession: Session | null = null;

      const result = session(customId, (sess) => {
        capturedSession = getCurrentSession();
        expect(sess.id).toBe(customId);
        return 'custom-result';
      });

      expect(result).toBe('custom-result');
      expect(capturedSession!.id).toBe(customId);
    });
  });

  describe('sessionAsync', () => {
    it('should run async callback within session context', async () => {
      let capturedSession: Session | null = null;

      const result = await sessionAsync(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        capturedSession = getCurrentSession();
        return 'async-result';
      });

      expect(result).toBe('async-result');
      expect(capturedSession).toBeTruthy();
      expect(capturedSession!.id).toMatch(/^[a-f0-9]{32}$/);
    });

    it('should run async callback with custom session ID', async () => {
      const customId = 'async-custom-id';
      let capturedSession: Session | null = null;

      const result = await sessionAsync(customId, async (sess) => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        capturedSession = getCurrentSession();
        expect(sess.id).toBe(customId);
        return 'async-custom-result';
      });

      expect(result).toBe('async-custom-result');
      expect(capturedSession!.id).toBe(customId);
    });
  });

  describe('getCurrentSession', () => {
    it('should return null when not in a session context', () => {
      const currentSession = getCurrentSession();
      expect(currentSession).toBe(null);
    });

    it('should return current session when in context', () => {
      session((sess) => {
        const currentSession = getCurrentSession();
        expect(currentSession).toBeTruthy();
        expect(currentSession!.id).toBe(sess.id);
      });
    });

    it('should maintain session across async boundaries', async () => {
      await sessionAsync(async (sess) => {
        const before = getCurrentSession();
        expect(before!.id).toBe(sess.id);

        await new Promise((resolve) => setTimeout(resolve, 10));

        const after = getCurrentSession();
        expect(after!.id).toBe(sess.id);
      });
    });
  });

  describe('withSession', () => {
    it('should run function within session context using ID', () => {
      const sessionId = 'with-session-id';
      let capturedSession: Session | null = null;

      const result = withSession(sessionId, () => {
        capturedSession = getCurrentSession();
        return 42;
      });

      expect(result).toBe(42);
      expect(capturedSession!.id).toBe(sessionId);
    });

    it('should run function within session context using session object', () => {
      const sess = { id: 'session-object-id' };
      let capturedSession: Session | null = null;

      const result = withSession(sess, () => {
        capturedSession = getCurrentSession();
        return 'object-result';
      });

      expect(result).toBe('object-result');
      expect(capturedSession!.id).toBe('session-object-id');
    });

    it('should handle null session ID', () => {
      let capturedSession: Session | null = null;

      const result = withSession(null, () => {
        capturedSession = getCurrentSession();
        return 'null-result';
      });

      expect(result).toBe('null-result');
      expect(capturedSession!.id).toBe(null);
    });
  });

  describe('withSessionAsync', () => {
    it('should run async function within session context', async () => {
      const sessionId = 'async-with-session';
      let capturedSession: Session | null = null;

      const result = await withSessionAsync(sessionId, async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        capturedSession = getCurrentSession();
        return 'async-with-result';
      });

      expect(result).toBe('async-with-result');
      expect(capturedSession!.id).toBe(sessionId);
    });

    it('should handle session object', async () => {
      const sess = { id: 'async-session-object' };
      let capturedSession: Session | null = null;

      const result = await withSessionAsync(sess, async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        capturedSession = getCurrentSession();
        return 'async-object-result';
      });

      expect(result).toBe('async-object-result');
      expect(capturedSession!.id).toBe('async-session-object');
    });
  });

  describe('nested sessions', () => {
    it('should properly handle nested session contexts', () => {
      const outerSessionId = 'outer-session';
      const innerSessionId = 'inner-session';

      withSession(outerSessionId, () => {
        const outer = getCurrentSession();
        expect(outer!.id).toBe(outerSessionId);

        withSession(innerSessionId, () => {
          const inner = getCurrentSession();
          expect(inner!.id).toBe(innerSessionId);
        });

        // Should restore outer session
        const afterInner = getCurrentSession();
        expect(afterInner!.id).toBe(outerSessionId);
      });

      // Should be null outside
      const outside = getCurrentSession();
      expect(outside).toBe(null);
    });

    it('should handle nested async sessions', async () => {
      await withSessionAsync('outer-async', async () => {
        const outer = getCurrentSession();
        expect(outer!.id).toBe('outer-async');

        await withSessionAsync('inner-async', async () => {
          const inner = getCurrentSession();
          expect(inner!.id).toBe('inner-async');
        });

        const afterInner = getCurrentSession();
        expect(afterInner!.id).toBe('outer-async');
      });
    });
  });
});
