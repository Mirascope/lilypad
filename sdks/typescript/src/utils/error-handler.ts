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
  
  // Use cause to preserve the original error information (ES2022+)
  // For older environments, this will be ignored but won't break
  try {
    return new Error(message, { cause: error });
  } catch {
    // Fallback for environments that don't support cause
    return new Error(message);
  }
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