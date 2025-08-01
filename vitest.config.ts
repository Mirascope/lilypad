import path from 'path';
import { coverageConfigDefaults, defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./tests/db-setup.ts', './tests/worker-setup.ts'],
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['db/**/*.ts', 'worker/**/*.ts'],
      exclude: [
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts',
        '**/migrations/**',
        'src/index.ts',
        'routeTree.gen.ts',
        'src/components/ui/**',
        'db/schema/**/*.ts',
        'worker/environment.ts',
        'worker/auth/oauth/types.ts',
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
    exclude: ['node_modules', 'dist', '.git', '.cache'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
