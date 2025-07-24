#!/usr/bin/env node
/**
 * Lilypad CLI tool for extracting TypeScript metadata
 *
 * This tool should be run as part of the user's build process to extract
 * TypeScript source code for versioned functions.
 *
 * Usage:
 *   npx lilypad-extract [options]
 *
 * Options:
 *   --project, -p    Path to tsconfig.json (default: ./tsconfig.json)
 *   --output, -o     Output path for metadata (default: ./lilypad-metadata.json)
 *   --include        Glob patterns to include (default: src/**&#47;*.ts)
 *   --watch, -w      Watch mode for development
 */

import { Command } from 'commander';
import path from 'path';
import fs from 'fs';
import chokidar from 'chokidar';
import { TypeScriptExtractor } from '../versioning/typescript-extractor';

const program = new Command();

program
  .name('lilypad-extract')
  .description('Extract TypeScript source code for Lilypad versioned functions')
  .version('0.1.0')
  .option('-p, --project <path>', 'Path to tsconfig.json', 'tsconfig.json')
  .option('-o, --output <path>', 'Output path for metadata', 'lilypad-metadata.json')
  .option('--include <patterns...>', 'Glob patterns to include')
  .option('-w, --watch', 'Watch mode for development', false)
  .option('--verbose', 'Verbose output', false);

program.parse();

const options = program.opts();

// Set default include patterns if not provided
if (!options.include || options.include.length === 0) {
  options.include = ['src/**/*.ts'];
}

async function extract() {
  const startTime = Date.now();
  const cwd = process.cwd();
  const tsConfigPath = path.resolve(cwd, options.project);
  const outputPath = path.resolve(cwd, options.output);

  if (options.verbose) {
    console.log('🔍 Lilypad TypeScript Extractor');
    console.log(`   Working directory: ${cwd}`);
    console.log(`   TypeScript config: ${tsConfigPath}`);
    console.log(`   Output path: ${outputPath}`);
    console.log(`   Include patterns: ${options.include.join(', ')}`);
  }

  // Check if tsconfig exists
  if (!fs.existsSync(tsConfigPath)) {
    console.error(`❌ Error: ${tsConfigPath} not found`);
    process.exit(1);
  }

  try {
    // Create extractor with user's patterns
    const extractor = new TypeScriptExtractor(
      path.dirname(tsConfigPath),
      path.basename(tsConfigPath),
      options.include,
    );

    // Extract metadata
    const metadata = extractor.extract();
    const functionCount = Object.keys(metadata.functions).length;

    // Save metadata
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));

    const elapsed = Date.now() - startTime;
    console.log(`✅ Extracted ${functionCount} versioned functions in ${elapsed}ms`);

    if (options.verbose && functionCount > 0) {
      console.log('\n📋 Extracted functions:');
      Object.values(metadata.functions).forEach((fn) => {
        console.log(`   - ${fn.name} (${fn.filePath}:${fn.startLine})`);
      });
    }

    return metadata;
  } catch (error) {
    console.error('❌ Error extracting metadata:', error);
    process.exit(1);
  }
}

async function watch() {
  console.log('👀 Watching for changes...');

  // Initial extraction
  await extract();

  // Watch for changes
  const watcher = chokidar.watch(options.include, {
    ignored: /(^|[/\\])\../, // ignore dotfiles
    persistent: true,
    cwd: process.cwd(),
  });

  watcher.on('change', async (filePath) => {
    console.log(`\n🔄 File changed: ${filePath}`);
    await extract();
  });

  watcher.on('add', async (filePath) => {
    console.log(`\n➕ File added: ${filePath}`);
    await extract();
  });

  watcher.on('unlink', async (filePath) => {
    console.log(`\n➖ File removed: ${filePath}`);
    await extract();
  });

  // Handle exit
  process.on('SIGINT', () => {
    console.log('\n👋 Stopping watch mode...');
    watcher.close();
    process.exit(0);
  });
}

// Main execution
if (options.watch) {
  watch().catch(console.error);
} else {
  extract()
    .then(() => process.exit(0))
    .catch(() => process.exit(1));
}
