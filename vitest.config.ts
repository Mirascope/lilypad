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
      include: ['db/**/*.ts', 'worker/**/*.ts'],
      exclude: [
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts',
        '**/migrations/**',
        '**/index.ts',
        'routeTree.gen.ts',
        'src/components/ui/**',
        ...coverageConfigDefaults.exclude,
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
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
