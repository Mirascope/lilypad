import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts', 'src/register.ts', 'src/register-otel.ts'],
  format: ['esm'],
  outDir: 'dist/modern',
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
  // Target modern Node.js versions for ESM build
  esbuildOptions: (options) => {
    options.platform = 'node';
    options.target = 'node20';
    options.resolveExtensions = ['.ts', '.js', '.json'];
  },
});
