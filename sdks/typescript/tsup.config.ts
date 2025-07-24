import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts', 'src/register.ts', 'src/register-otel.ts', 'src/cli/lilypad-extract.ts'],
  format: ['cjs', 'esm'],
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
  // Include the generated client in the build
  esbuildOptions: (options) => {
    options.platform = 'node';
    options.resolveExtensions = ['.ts', '.js', '.json'];
  },
});
