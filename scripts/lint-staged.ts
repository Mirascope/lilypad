#!/usr/bin/env bun

/**
 * Script to run TypeScript type checking regardless of what files were changed
 * This ensures we check the entire project graph, not just modified files
 *
 * Usage from lint-staged: "*.{ts,tsx}": ["bun run scripts/lint-staged.ts"]
 */

import { execSync } from 'child_process';

console.log('Running TypeScript check on the entire project...');

try {
  execSync('bun run typecheck', { stdio: 'inherit' });
  console.log('TypeScript check passed');
} catch (error) {
  console.error('TypeScript check failed!');
  process.exit(1);
}

console.log('Running ESLint to lint and fix the entire project...');

try {
  execSync('bun run lint:eslint:fix', { stdio: 'inherit' });
  console.log('Project linted and fixed!');
} catch (error) {
  console.error('Linting failed!');
  process.exit(1);
}
