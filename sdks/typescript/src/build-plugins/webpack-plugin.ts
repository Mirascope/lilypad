/**
 * Webpack Plugin for Lilypad TypeScript Extraction
 *
 * Automatically extracts TypeScript source code during webpack builds.
 *
 * Usage:
 * ```js
 * const { LilypadWebpackPlugin } = require('@lilypad/typescript-sdk/webpack');
 *
 * module.exports = {
 *   plugins: [
 *     new LilypadWebpackPlugin({
 *       // options
 *     })
 *   ]
 * };
 * ```
 */

import type { Compiler, WebpackPluginInstance } from 'webpack';
import path from 'path';
import fs from 'fs';
import { TypeScriptExtractor } from '../versioning/typescript-extractor';

export interface LilypadWebpackPluginOptions {
  /**
   * Path to tsconfig.json
   * @default './tsconfig.json'
   */
  tsConfig?: string;

  /**
   * Output filename for metadata
   * @default 'lilypad-metadata.json'
   */
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

export class LilypadWebpackPlugin implements WebpackPluginInstance {
  private options: Required<LilypadWebpackPluginOptions>;

  constructor(options: LilypadWebpackPluginOptions = {}) {
    this.options = {
      tsConfig: options.tsConfig || './tsconfig.json',
      output: options.output || 'lilypad-metadata.json',
      include: options.include || ['src/**/*.ts', 'src/**/*.tsx'],
      verbose: options.verbose || false,
    };
  }

  apply(compiler: Compiler): void {
    const pluginName = 'LilypadWebpackPlugin';

    // Extract metadata before compilation starts
    compiler.hooks.beforeCompile.tapAsync(pluginName, async (_params, callback: any) => {
      try {
        await this.extractMetadata(compiler);
        callback();
      } catch (error) {
        callback(error as Error);
      }
    });

    // Include metadata in build output
    compiler.hooks.emit.tapAsync(pluginName, (compilation: any, callback: any) => {
      const metadataPath = path.resolve(compiler.context, this.options.output);

      if (fs.existsSync(metadataPath)) {
        const metadata = fs.readFileSync(metadataPath, 'utf-8');

        // Add metadata file to webpack output
        compilation.assets[this.options.output] = {
          source: () => metadata,
          size: () => metadata.length,
        };

        if (this.options.verbose) {
          console.log(`[Lilypad] Added ${this.options.output} to build output`);
        }
      }

      callback();
    });
  }

  private async extractMetadata(compiler: Compiler): Promise<void> {
    const context = compiler.context;
    const tsConfigPath = path.resolve(context, this.options.tsConfig);

    if (!fs.existsSync(tsConfigPath)) {
      if (this.options.verbose) {
        console.warn(`[Lilypad] TypeScript config not found: ${tsConfigPath}`);
      }
      return;
    }

    if (this.options.verbose) {
      console.log('[Lilypad] Extracting TypeScript metadata...');
    }

    try {
      const extractor = new TypeScriptExtractor(
        path.dirname(tsConfigPath),
        path.basename(tsConfigPath),
        this.options.include,
      );

      const metadata = extractor.extract();
      const functionCount = Object.keys(metadata.functions).length;

      // Save metadata
      const outputPath = path.resolve(context, this.options.output);
      const outputDir = path.dirname(outputPath);

      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));

      if (this.options.verbose) {
        console.log(`[Lilypad] Extracted ${functionCount} versioned functions`);
      }
    } catch (error) {
      console.error('[Lilypad] Error extracting metadata:', error);
      // Don't fail the build, just warn
    }
  }
}
