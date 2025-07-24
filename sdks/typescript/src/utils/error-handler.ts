/**
 * Global error handler for background async operations
 */

import { logger } from './logger';

export type ErrorHandler = (error: Error, context?: Record<string, unknown>) => void;

let globalErrorHandler: ErrorHandler | null = null;

/**
 * Ensures error is an Error object, preserving original error as cause
 */
export function ensureError(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  }

  const message = typeof error === 'string' ? error : String(error);

  // Create error with message
  const err = new Error(message);

  // Try to add cause property if supported
  try {
    Object.defineProperty(err, 'cause', {
      value: error,
      enumerable: false,
      writable: true,
      configurable: true,
    });
  } catch {
    // Ignore if property definition fails
  }

  return err;
}

/**
 * Set a global error handler for background operations
 */
export function setGlobalErrorHandler(handler: ErrorHandler | null): void {
  globalErrorHandler = handler;
}

/**
 * Handle background operation errors
 */
export function handleBackgroundError(error: unknown, context?: Record<string, unknown>): void {
  const errorObj = ensureError(error);

  // Call custom handler if set
  if (globalErrorHandler) {
    try {
      globalErrorHandler(errorObj, context);
    } catch (handlerError) {
      logger.error('Error in global error handler:', handlerError);
    }
  }

  // Always log the error
  logger.error('Background operation error:', errorObj, context);
}
