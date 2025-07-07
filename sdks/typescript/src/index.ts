/**
 * Lilypad TypeScript SDK
 *
 * LLM observability and monitoring for TypeScript/JavaScript applications
 */

import { configure } from './configure';
import { shutdown } from './shutdown';

export { configure } from './configure';
export { shutdown } from './shutdown';
export type { LilypadConfig, LogLevel } from './types';

// Default export for convenience
const lilypad = {
  configure,
  shutdown,
};

export default lilypad;
