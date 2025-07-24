import { defineConfig } from 'vite';
import { lilypadPlugin } from '@lilypad/typescript-sdk/vite';

export default defineConfig({
  plugins: [
    lilypadPlugin({
      tsConfig: './tsconfig.json',
      output: 'lilypad-metadata.json',
      include: ['src/**/*.ts'],
      verbose: true,
    }),
  ],
  build: {
    lib: {
      entry: 'src/index.ts',
      formats: ['es'],
      fileName: 'index',
    },
    rollupOptions: {
      external: ['@lilypad/typescript-sdk'],
    },
  },
});
