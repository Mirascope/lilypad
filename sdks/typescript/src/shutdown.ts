import { isConfigured, setSettings } from './utils/settings';
import { logger } from './utils/logger';
import { trace } from '@opentelemetry/api';

let shutdownPromise: Promise<void> | null = null;
let isShuttingDown = false;

export function isSDKShuttingDown(): boolean {
  return isShuttingDown;
}

/**
 * Shutdown the Lilypad SDK gracefully
 * @returns Promise that resolves when shutdown is complete
 */
export async function shutdown(): Promise<void> {
  // Prevent multiple simultaneous shutdowns
  if (shutdownPromise) {
    return shutdownPromise;
  }

  isShuttingDown = true;
  shutdownPromise = performShutdown();
  return shutdownPromise;
}

async function performShutdown(): Promise<void> {
  logger.info('Shutting down Lilypad SDK...');

  if (!isConfigured()) {
    logger.debug('Shutdown called but SDK not configured.');
    return;
  }

  try {
    // Get the tracer provider and shut it down
    const tracerProvider = trace.getTracerProvider();

    // Check if it has a shutdown method (it should if it's our configured provider)
    if ('shutdown' in tracerProvider && typeof tracerProvider.shutdown === 'function') {
      await tracerProvider.shutdown();
      logger.info('Lilypad SDK shut down successfully.');
    } else {
      logger.warn('Tracer provider does not support shutdown.');
    }
  } catch (error) {
    logger.error('Error during Lilypad SDK shutdown:', error);
  } finally {
    // Clear the settings to mark as unconfigured
    setSettings(null);
    shutdownPromise = null;
    isShuttingDown = false;
  }
}

// Register shutdown handlers for graceful termination
// Note: Automatic registration can be disabled by setting LILYPAD_DISABLE_AUTO_SHUTDOWN=true
if (typeof process !== 'undefined' && process.env.LILYPAD_DISABLE_AUTO_SHUTDOWN !== 'true') {
  const shutdownHandler = (signal: string) => {
    logger.info(`Received ${signal}, initiating graceful shutdown...`);
    shutdown()
      .catch((err) => logger.error('Error in shutdown handler:', err))
      .finally(() => process.exit(0));
  };

  // Only register once
  if (!process.listeners('SIGTERM').length) {
    process.once('SIGTERM', () => shutdownHandler('SIGTERM'));
  }
  if (!process.listeners('SIGINT').length) {
    process.once('SIGINT', () => shutdownHandler('SIGINT'));
  }

  // Also handle unexpected exits
  if (!process.listeners('beforeExit').length) {
    process.once('beforeExit', async (code) => {
      if (code === 0) {
        logger.debug('Process exiting normally, flushing spans...');
        await shutdown();
      }
    });
  }
}
