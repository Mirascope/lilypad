import { describe, expect, it } from 'vitest';
import { getSessionFromCookie } from './utils';

describe('getSessionFromCookie', () => {
  it('should return null when no Cookie header is present', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers(),
    });
    expect(getSessionFromCookie(request)).toBeNull();
  });

  it('should return null when Cookie header is empty', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({ Cookie: '' }),
    });
    expect(getSessionFromCookie(request)).toBeNull();
  });

  it('should return session value when session cookie exists', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({ Cookie: 'session=test-session-value' }),
    });
    expect(getSessionFromCookie(request)).toBe('test-session-value');
  });

  it('should return session value when multiple cookies exist', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({
        Cookie: 'other=value; session=test-session-value; another=value2',
      }),
    });
    expect(getSessionFromCookie(request)).toBe('test-session-value');
  });

  it('should return null when cookie name has trailing space', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({ Cookie: 'session = test-session-value' }),
    });
    expect(getSessionFromCookie(request)).toBeNull();
  });

  it('should handle cookies with spaces after semicolon', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({
        Cookie: 'other=value;  session=test-session-value;  another=value2',
      }),
    });
    expect(getSessionFromCookie(request)).toBe('test-session-value');
  });

  it('should return null when session cookie has no value', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({ Cookie: 'session=' }),
    });
    expect(getSessionFromCookie(request)).toBeNull();
  });

  it('should return null when session cookie is malformed', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({ Cookie: 'session' }),
    });
    expect(getSessionFromCookie(request)).toBeNull();
  });

  it('should handle session as the last cookie without trailing semicolon', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({
        Cookie: 'other=value; another=value2; session=test-session-value',
      }),
    });
    expect(getSessionFromCookie(request)).toBe('test-session-value');
  });

  it('should be case-sensitive for cookie name', () => {
    const request = new Request('http://localhost:3000', {
      headers: new Headers({ Cookie: 'Session=test-session-value' }),
    });
    expect(getSessionFromCookie(request)).toBeNull();
  });
});
