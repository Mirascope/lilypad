import { AsyncLocalStorage } from 'node:async_hooks';
import { randomUUID } from 'node:crypto';

/**
 * Lightweight container for a session identifier.
 */
export interface Session {
  id: string | null;
}

/**
 * AsyncLocalStorage for maintaining session context across async boundaries
 */
export const SESSION_CONTEXT = new AsyncLocalStorage<Session | null>();

/**
 * Generate a new 32-char hexadecimal session ID
 */
export function generateSessionId(): string {
  return randomUUID().replace(/-/g, '');
}

/**
 * Create a Session context.
 *
 * @param id - Optional session ID. If not provided, a new ID will be generated.
 * @returns Session object
 *
 * @example
 * ```ts
 * // Create a new session with auto-generated ID
 * const sess = session();
 * console.log(sess.id);
 *
 * // Create a session with specific ID
 * const sess2 = session('custom-session-id');
 *
 * // Use with callback
 * session((sess) => {
 *   // Your code runs within this session context
 *   console.log('Session ID:', sess.id);
 * });
 * ```
 */
export function session(id?: string | null): Session;
export function session<T>(callback: (session: Session) => T): T;
export function session<T>(id: string | null, callback: (session: Session) => T): T;
export function session<T>(
  idOrCallback?: string | null | ((session: Session) => T),
  callback?: (session: Session) => T,
): Session | T {
  // Determine arguments
  let sessionId: string | null;
  let cb: ((session: Session) => T) | undefined;

  if (typeof idOrCallback === 'function') {
    sessionId = generateSessionId();
    cb = idOrCallback;
  } else {
    sessionId = idOrCallback === undefined ? generateSessionId() : idOrCallback;
    cb = callback;
  }

  const sessionObj: Session = { id: sessionId };

  // If no callback, just return the session
  if (!cb) {
    return sessionObj;
  }

  // Run callback within session context
  return SESSION_CONTEXT.run(sessionObj, () => cb(sessionObj));
}

/**
 * Create a Session context for async operations.
 *
 * @param id - Optional session ID. If not provided, a new ID will be generated.
 * @returns Session object
 *
 * @example
 * ```ts
 * // Use with async callback
 * await sessionAsync(async (sess) => {
 *   console.log('Session ID:', sess.id);
 *   await someAsyncOperation();
 * });
 *
 * // With custom ID
 * await sessionAsync('custom-id', async (sess) => {
 *   await someAsyncOperation();
 * });
 * ```
 */
export async function sessionAsync<T>(callback: (session: Session) => Promise<T>): Promise<T>;
export async function sessionAsync<T>(
  id: string | null,
  callback: (session: Session) => Promise<T>,
): Promise<T>;
export async function sessionAsync<T>(
  idOrCallback: string | null | ((session: Session) => Promise<T>),
  callback?: (session: Session) => Promise<T>,
): Promise<T> {
  // Determine arguments
  let sessionId: string | null;
  let cb: (session: Session) => Promise<T>;

  if (typeof idOrCallback === 'function') {
    sessionId = generateSessionId();
    cb = idOrCallback;
  } else {
    sessionId = idOrCallback === undefined ? generateSessionId() : idOrCallback;
    cb = callback!;
  }

  const sessionObj: Session = { id: sessionId };

  // Run async callback within session context
  return SESSION_CONTEXT.run(sessionObj, () => cb(sessionObj));
}

/**
 * Get the current session from async context
 *
 * @returns Current session or null if not in a session context
 *
 * @example
 * ```ts
 * const currentSession = getCurrentSession();
 * if (currentSession) {
 *   console.log('Current session ID:', currentSession.id);
 * }
 * ```
 */
export function getCurrentSession(): Session | null {
  return SESSION_CONTEXT.getStore() ?? null;
}

/**
 * Run a function within a session context
 *
 * @param sessionOrId - Session object or session ID
 * @param fn - Function to run within the session context
 * @returns Result of the function
 *
 * @example
 * ```ts
 * const result = withSession('my-session-id', () => {
 *   // This code runs within the session context
 *   return computeSomething();
 * });
 * ```
 */
export function withSession<T>(sessionOrId: Session | string | null, fn: () => T): T {
  const sessionObj: Session =
    typeof sessionOrId === 'string' || sessionOrId === null ? { id: sessionOrId } : sessionOrId;
  return SESSION_CONTEXT.run(sessionObj, fn);
}

/**
 * Run an async function within a session context
 *
 * @param sessionOrId - Session object or session ID
 * @param fn - Async function to run within the session context
 * @returns Promise with the result of the function
 *
 * @example
 * ```ts
 * const result = await withSessionAsync('my-session-id', async () => {
 *   // This async code runs within the session context
 *   return await fetchSomething();
 * });
 * ```
 */
export async function withSessionAsync<T>(
  sessionOrId: Session | string | null,
  fn: () => Promise<T>,
): Promise<T> {
  const sessionObj: Session =
    typeof sessionOrId === 'string' || sessionOrId === null ? { id: sessionOrId } : sessionOrId;
  return SESSION_CONTEXT.run(sessionObj, fn);
}
