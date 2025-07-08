/**
 * Register script for auto-instrumentation
 * This file should be loaded with --require or --loader flag
 */
import { logger } from './utils/logger';

// Enable debug logging if configured
logger.setLevel((process.env.LILYPAD_LOG_LEVEL as any) || 'info');

// Hook into require early
// eslint-disable-next-line @typescript-eslint/no-var-requires
const Module = require('module');
const originalRequire = Module.prototype.require;

// Track if we've already patched OpenAI
let openaiPatched = false;

// Override require
Module.prototype.require = function (id: string, ...args: any[]) {
  const exports = originalRequire.apply(this, [id, ...args]);

  // Check if this is OpenAI being required
  if (id === 'openai' && !openaiPatched) {
    logger.debug('[Register] Intercepting OpenAI require');
    openaiPatched = true;
    return patchOpenAI(exports);
  }

  return exports;
};

// Also hook into import for ESM
if (typeof process !== 'undefined' && process.versions && process.versions.node) {
  const majorVersion = parseInt(process.versions.node.split('.')[0], 10);

  // For Node.js 14.8+ we can use experimental loader hooks
  if (majorVersion >= 14) {
    // Store original dynamic import
    const globalAny = globalThis as any;
    const originalImport =
      globalAny.import ||
      (globalAny.import = async (specifier: string) => {
        return originalRequire(specifier);
      });

    // Override dynamic import
    globalAny.import = async function (specifier: string) {
      if (specifier === 'openai' && !openaiPatched) {
        logger.debug('[Register] Intercepting OpenAI dynamic import');
        const exports = await originalImport.call(this, specifier);
        openaiPatched = true;
        return patchOpenAI(exports);
      }
      return originalImport.call(this, specifier);
    };
  }
}

function patchOpenAI(exports: any): any {
  logger.debug('[Register] Patching OpenAI exports, type:', typeof exports);

  // In CommonJS, OpenAI exports like: module.exports = OpenAI; module.exports.default = OpenAI;
  // So the main export is the function itself
  if (typeof exports === 'function') {
    logger.debug('[Register] exports is a function (CommonJS default pattern)');
    const OriginalOpenAI = exports;

    // Return a proxy that intercepts construction
    const ProxiedOpenAI = new Proxy(OriginalOpenAI, {
      construct(target, args) {
        logger.debug('[Register] Intercepting OpenAI constructor (main export)');
        const instance = new target(...args);
        patchOpenAIInstance(instance);
        return instance;
      },
      // Forward all other operations
      get(target, prop) {
        return target[prop];
      },
    });

    // Copy all properties from original to proxy
    for (const key in exports) {
      if (Object.prototype.hasOwnProperty.call(exports, key)) {
        ProxiedOpenAI[key] = exports[key];
      }
    }

    // Make sure default points to the proxy too
    if ('default' in ProxiedOpenAI) {
      ProxiedOpenAI.default = ProxiedOpenAI;
    }

    return ProxiedOpenAI;
  }

  // Handle ES module style exports
  if (exports && typeof exports === 'object') {
    // Patch default export
    if (exports.default && typeof exports.default === 'function') {
      logger.debug('[Register] Found exports.default');
      const OriginalOpenAI = exports.default;

      exports.default = new Proxy(OriginalOpenAI, {
        construct(target, args) {
          logger.debug('[Register] Intercepting OpenAI constructor (default export)');
          const instance = new target(...args);
          patchOpenAIInstance(instance);
          return instance;
        },
        get(target, prop) {
          return target[prop];
        },
      });
    }

    // Also patch named export if it exists
    if (exports.OpenAI && typeof exports.OpenAI === 'function') {
      logger.debug('[Register] Found exports.OpenAI (named export)');
      const OriginalOpenAI = exports.OpenAI;

      exports.OpenAI = new Proxy(OriginalOpenAI, {
        construct(target, args) {
          logger.debug('[Register] Intercepting OpenAI constructor (named export)');
          const instance = new target(...args);
          patchOpenAIInstance(instance);
          return instance;
        },
        get(target, prop) {
          return target[prop];
        },
      });
    }
  }

  return exports;
}

function patchOpenAIInstance(instance: any): void {
  logger.debug('[Register] Patching OpenAI instance');

  if (!instance.chat?.completions?.create) {
    logger.warn('[Register] chat.completions.create not found on instance');
    return;
  }

  const original = instance.chat.completions.create;

  instance.chat.completions.create = async function (...args: any[]) {
    // Lazy load the instrumentation to avoid circular dependencies
    const { instrumentOpenAICall } = await import('./instrumentors/openai-instrumentation');
    return instrumentOpenAICall(original.bind(this), args);
  };

  logger.debug('[Register] Successfully patched chat.completions.create');
}

logger.debug('[Register] Lilypad OpenAI auto-instrumentation register loaded');
