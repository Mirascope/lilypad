import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./src/test-utils/setup.ts'],
    exclude: ['node_modules', 'dist', 'dist-examples', '**/*.d.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'dist/',
        'dist-examples/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts',
        'test/**',
        'examples/**',
        'src/test-utils/**',
        'src/**/*.test.ts',
        'src/**/*.integration.test.ts',
        'lilypad/**',
        'lilypad/generated/**',
        // Type-only files
        'src/types.ts',
        'src/types/**',
      ],
    },
  },
});
