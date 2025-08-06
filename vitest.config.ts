import path from 'path';
import { coverageConfigDefaults, defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: false,
    environment: 'node',
    globalSetup: './tests/db/global.ts',
    setupFiles: './tests/db/setup.ts',
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['db', 'worker'],
      exclude: [
        '**/index.ts',
        '**/schemas.ts',
        'db/schema',
        'worker/api', // excluding while we work on migrating to OpenAPI + 100% coverage
        'worker/auth', // excluding while we work on migrating to OpenAPI + 100% coverage
        ...coverageConfigDefaults.exclude,
      ],
      thresholds: {
        global: {
          branches: 100,
          functions: 100,
          lines: 100,
          statements: 100,
        },
      },
    },
    exclude: ['**/node_modules/**', 'dist', '.git', '.cache', 'sdks/**'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
