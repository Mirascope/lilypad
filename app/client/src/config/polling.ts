/**
 * Configuration for real-time polling feature
 */

export const POLLING_CONFIG = {
  // Default polling interval in milliseconds
  DEFAULT_INTERVAL: Number(import.meta.env.VITE_POLLING_INTERVAL) || 5000,
  
  // Whether polling is enabled by default
  ENABLED_BY_DEFAULT: import.meta.env.VITE_ENABLE_POLLING === 'true',
  
  // Maximum number of consecutive errors before stopping
  MAX_CONSECUTIVE_ERRORS: 3,
  
  // Exponential backoff multiplier for errors
  ERROR_BACKOFF_MULTIPLIER: 2,
  
  // Maximum backoff time in milliseconds
  MAX_BACKOFF_MS: 30000,
  
  // Maximum number of span IDs to keep for deduplication
  MAX_SEEN_SPAN_IDS: 1000,
  
  // Number of span IDs to keep when cleaning up
  CLEANUP_KEEP_COUNT: 500,
} as const;

export type PollingConfig = typeof POLLING_CONFIG;