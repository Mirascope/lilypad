/**
 * Shared context manager singleton to ensure consistent context propagation
 * across register.js and configure() initialization paths
 */

import { AsyncLocalStorageContextManager } from '@opentelemetry/context-async-hooks';
import { context, ContextManager } from '@opentelemetry/api';
import { logger } from './logger';

// Global singleton instance
let globalContextManager: AsyncLocalStorageContextManager | null = null;

/**
 * Get or create the global context manager singleton
 * This ensures both register.js and configure() use the same context manager
 */
export function getOrCreateContextManager(): ContextManager {
  if (!globalContextManager) {
    logger.debug('Creating new global AsyncLocalStorageContextManager');
    globalContextManager = new AsyncLocalStorageContextManager();
    
    // Enable and set as global context manager
    const enabled = globalContextManager.enable();
    context.setGlobalContextManager(enabled);
    
    logger.debug('Global context manager initialized and set');
  } else {
    logger.debug('Reusing existing global context manager');
  }
  
  return globalContextManager;
}

/**
 * Check if a global context manager is already initialized
 */
export function hasGlobalContextManager(): boolean {
  return globalContextManager !== null;
}

/**
 * Get the current global context manager if it exists
 */
export function getGlobalContextManager(): ContextManager | null {
  return globalContextManager;
}