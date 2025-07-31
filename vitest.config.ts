import path from 'path';
import { coverageConfigDefaults, defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: false,
    environment: 'node',
    setupFiles: './tests/setup.ts',
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['db/**/*.ts'],
      exclude: [
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts',
        '**/migrations/**',
        '**/index.ts',
        'routeTree.gen.ts',
        'src/**',
        'worker/**/*.ts',
        'db/schema/**/*.ts',
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
