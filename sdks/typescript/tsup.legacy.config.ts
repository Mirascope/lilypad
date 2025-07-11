import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts', 'src/register.ts', 'src/register-otel.ts'],
  format: ['cjs'],
  outDir: 'dist/legacy',
  dts: {
    compilerOptions: {
      // Disable isolatedModules for declaration generation only
      isolatedModules: false,
    },
  },
  sourcemap: true,
  clean: true,
  minify: false,
  splitting: false,
  treeshake: false, // Disable tree shaking to preserve side effects in register.ts
  external: ['openai'],
  noExternal: ['@opentelemetry/*', './lilypad/generated/**'],
  // Target older Node.js versions for legacy build
  esbuildOptions: (options) => {
    options.platform = 'node';
    options.target = 'node18';
    options.resolveExtensions = ['.ts', '.js', '.json'];
  },
});
