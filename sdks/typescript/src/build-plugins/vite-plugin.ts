/**
 * Vite plugin that extracts TypeScript source code during builds.
 */

import type { Plugin } from 'vite';
import path from 'path';
import fs from 'fs';
import { TypeScriptExtractor } from '../versioning/typescript-extractor';

export interface LilypadVitePluginOptions {
  /** @default './tsconfig.json' */
  tsConfig?: string;

  /** @default 'lilypad-metadata.json' */
  output?: string;

  /**
   * Include patterns
   * @default ["src/**&#47;*.ts", "src/**&#47;*.tsx"]
   */
  include?: string[];

  /**
   * Enable verbose logging
   * @default false
   */
  verbose?: boolean;
}

export function lilypadPlugin(options: LilypadVitePluginOptions = {}): Plugin {
  const opts: Required<LilypadVitePluginOptions> = {
    tsConfig: options.tsConfig || './tsconfig.json',
    output: options.output || 'lilypad-metadata.json',
    include: options.include || ['src/**/*.ts', 'src/**/*.tsx'],
    verbose: options.verbose || false,
  };

  let rootDir: string;
  let metadata: import('../versioning/typescript-extractor').VersioningMetadata | null = null;

  return {
    name: 'vite-plugin-lilypad',

    configResolved(config) {
      rootDir = config.root;
    },

    async buildStart() {
      const tsConfigPath = path.resolve(rootDir, opts.tsConfig);

      if (!fs.existsSync(tsConfigPath)) {
        if (opts.verbose) {
          this.warn(`TypeScript config not found: ${tsConfigPath}`);
        }
        return;
      }

      if (opts.verbose) {
        console.log('[Lilypad] Extracting TypeScript metadata...');
      }

      try {
        const extractor = new TypeScriptExtractor(
          path.dirname(tsConfigPath),
          path.basename(tsConfigPath),
          opts.include,
        );

        metadata = extractor.extract();
        const functionCount = Object.keys(metadata.functions).length;

        if (opts.verbose) {
          console.log(`[Lilypad] Extracted ${functionCount} versioned functions`);
        }
      } catch (error) {
        this.error(`Error extracting Lilypad metadata: ${error}`);
      }
    },

    generateBundle() {
      if (!metadata) return;

      // Emit metadata as an asset
      this.emitFile({
        type: 'asset',
        fileName: opts.output,
        source: JSON.stringify(metadata, null, 2),
      });

      // Also save to root for development
      const outputPath = path.resolve(rootDir, opts.output);
      fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));
    },

    // Development server support
    configureServer(server) {
      // Watch TypeScript files for changes
      server.watcher.add(opts.include);

      server.watcher.on('change', async (file) => {
        if (file.endsWith('.ts') || file.endsWith('.tsx')) {
          try {
            const tsConfigPath = path.resolve(rootDir, opts.tsConfig);
            const extractor = new TypeScriptExtractor(
              path.dirname(tsConfigPath),
              path.basename(tsConfigPath),
              opts.include,
            );

            metadata = extractor.extract();

            // Save for development
            const outputPath = path.resolve(rootDir, opts.output);
            fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));

            if (opts.verbose) {
              const functionCount = Object.keys(metadata.functions).length;
              console.log(`[Lilypad] Re-extracted ${functionCount} functions`);
            }
          } catch (error) {
            console.error('[Lilypad] Error re-extracting metadata:', error);
          }
        }
      });
    },
  };
}
