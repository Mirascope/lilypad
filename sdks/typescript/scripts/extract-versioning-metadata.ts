#!/usr/bin/env tsx
/**
 * Build script to extract TypeScript source code for versioned functions
 *
 * This script runs during the build process to create a metadata file
 * containing the original TypeScript source code for all versioned functions.
 */

import { TypeScriptExtractor } from '../src/versioning/typescript-extractor';
import * as path from 'path';
import * as fs from 'fs';

const rootDir = path.resolve(__dirname, '..');
const outputDir = path.join(rootDir, 'dist');
const outputPath = path.join(outputDir, 'versioning-metadata.json');

console.log('🔍 Extracting versioned functions metadata...');
console.log(`   Root directory: ${rootDir}`);
console.log(`   Output path: ${outputPath}`);

try {
  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Create extractor and process files
  const extractor = new TypeScriptExtractor(rootDir, 'tsconfig.json');
  const metadata = extractor.extract();

  // Save metadata
  fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));

  // Print summary
  const functionCount = Object.keys(metadata.functions).length;
  console.log(`✅ Successfully extracted ${functionCount} versioned functions`);

  if (functionCount > 0) {
    console.log('\n📋 Extracted functions:');
    Object.values(metadata.functions).forEach((fn) => {
      console.log(`   - ${fn.name} (${fn.filePath}:${fn.startLine})`);
    });
  }

  // Also create a copy in src for development
  const devOutputPath = path.join(rootDir, 'src', 'versioning', 'metadata.json');
  fs.writeFileSync(devOutputPath, JSON.stringify(metadata, null, 2));
  console.log(`\n📁 Development copy saved to: ${devOutputPath}`);
} catch (error) {
  console.error('❌ Error extracting metadata:', error);
  process.exit(1);
}
