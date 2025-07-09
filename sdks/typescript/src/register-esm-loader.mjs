/**
 * ESM Loader for auto-instrumentation
 * This file should be loaded with --loader flag (Node.js < 18.19) or --import flag (Node.js >= 18.19)
 *
 * Usage:
 *   Node.js < 18.19: node --loader ./register-esm-loader.mjs app.js
 *   Node.js >= 18.19: node --import ./register-esm-loader.mjs app.js
 */

import { register } from 'module';
import { pathToFileURL } from 'url';
import { createRequire } from 'module';

// Check Node.js version to determine the correct hook API
const nodeVersion = process.versions.node.split('.').map(Number);
const isNode20Plus = nodeVersion[0] > 20 || (nodeVersion[0] === 20 && nodeVersion[1] >= 0);

if (isNode20Plus) {
  // Node.js 20+ uses the register API
  register('./esm-hooks.mjs', pathToFileURL(new URL('.', import.meta.url).href));
} else {
  // Node.js < 20 exports the hooks directly
  const require = createRequire(import.meta.url);
  const { logger } = require('./utils/logger');

  logger.info('[ESM Loader] Initializing ESM hooks for OpenAI instrumentation');

  // Re-export hooks from esm-hooks.mjs
  const hooks = await import('./esm-hooks.mjs');
  export const resolve = hooks.resolve;
  export const load = hooks.load;
}

// Initialize the instrumentation immediately
const initInstrumentation = async () => {
  const require = createRequire(import.meta.url);
  const { logger } = require('./utils/logger');

  logger.info('[ESM Loader] Loading register module');

  // Import the CommonJS register module
  await import('./register.js');
};

// Initialize but don't block module loading
initInstrumentation().catch((err) => {
  const require = createRequire(import.meta.url);
  const { logger } = require('./utils/logger');
  logger.error('[ESM Loader] Failed to initialize instrumentation:', err);
});
