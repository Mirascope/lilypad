/**
 * ESM Hooks for OpenAI instrumentation
 * These hooks intercept ESM module loading to apply instrumentation
 */

import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const { logger } = require('./utils/logger');
const { OpenAIInstrumentation } = require('./instrumentors/openai-otel-instrumentation');

// Track if we've already instrumented OpenAI
let openAIInstrumented = false;
let openAIInstrumentation = null;

/**
 * Resolve hook - intercepts module resolution
 * @param {string} specifier - The module specifier
 * @param {object} context - The resolve context
 * @param {Function} nextResolve - The next resolve hook in the chain
 */
export async function resolve(specifier, context, nextResolve) {
  // Let Node.js handle the resolution
  const result = await nextResolve(specifier, context);

  // Mark OpenAI modules for special handling
  if (specifier === 'openai' || specifier.startsWith('openai/')) {
    result.format = 'openai-instrumented';
  }

  return result;
}

/**
 * Load hook - intercepts module loading
 * @param {string} url - The resolved module URL
 * @param {object} context - The load context
 * @param {Function} nextLoad - The next load hook in the chain
 */
export async function load(url, context, nextLoad) {
  // Check if this is an OpenAI module
  if (context.format === 'openai-instrumented') {
    logger.info('[ESM Hooks] Intercepting OpenAI module load:', url);

    // Load the original module
    const original = await nextLoad(url, { ...context, format: undefined });

    // Apply instrumentation wrapper
    if (!openAIInstrumented) {
      openAIInstrumented = true;

      // Create instrumentation instance if not exists
      if (!openAIInstrumentation) {
        openAIInstrumentation = new OpenAIInstrumentation({
          requestHook: (span, params) => {
            logger.debug('[ESM Hooks] Request hook called', { model: params.model });
          },
          responseHook: (span, response) => {
            logger.debug('[ESM Hooks] Response hook called', { id: response.id });
          },
          fallbackToProxy: true,
        });
      }

      // Wrap the module exports
      return {
        format: original.format,
        shortCircuit: true,
        source: `
          import { createRequire } from 'module';
          const require = createRequire(import.meta.url);
          
          // Import original module
          const originalModule = await import('${url}');
          
          // Get instrumentation
          const { OpenAIInstrumentation } = require('${new URL('./instrumentors/openai-otel-instrumentation.js', import.meta.url).href}');
          const instrumentation = new OpenAIInstrumentation({
            fallbackToProxy: true,
          });
          
          // Apply instrumentation
          const wrappedExports = instrumentation._applyPatch(originalModule);
          
          // Re-export everything
          export * from '${url}';
          export default wrappedExports.default || wrappedExports;
        `,
      };
    }
  }

  // Let Node.js handle all other modules
  return nextLoad(url, context);
}

/**
 * Initialize hook - called when the loader is registered (Node.js 20.6+)
 */
export async function initialize() {
  const { logger } = require('./utils/logger');
  logger.info('[ESM Hooks] ESM loader initialized for OpenAI instrumentation');
}
