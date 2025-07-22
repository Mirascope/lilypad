/**
 * Simple extraction script for the demo
 * This runs the TypeScript extractor as a build step
 */

// Since TypeScriptExtractor uses ts-morph which is a dev dependency,
// we'll use tsx to run the TypeScript version directly
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🔍 Extracting TypeScript code...');

try {
  // Create a temporary TypeScript extraction script
  const extractScript = `
import { TypeScriptExtractor } from '../../src/versioning/typescript-extractor';
import fs from 'fs';
import path from 'path';

const extractor = new TypeScriptExtractor(
  '${__dirname}',
  'tsconfig.json',
  ['src/**/*.ts']
);

console.log('Extracting from directory:', '${__dirname}');
console.log('Include patterns:', ['src/**/*.ts']);

try {
  const metadata = extractor.extract();
  console.log('Extraction completed, found functions:', Object.keys(metadata.functions || {}));
} catch (error) {
  console.error('Extraction error:', error);
  throw error;
}

const metadata = extractor.extract();
const outputPath = path.join('${__dirname}', 'lilypad-metadata.json');
fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));

console.log(\`✅ Extracted \${Object.keys(metadata.functions).length} versioned functions\`);
if (Object.keys(metadata.functions).length > 0) {
  console.log('\\n📋 Functions:');
  Object.values(metadata.functions).forEach((fn: any) => {
    console.log(\`   - \${fn.name} (\${fn.filePath}:\${fn.startLine})\`);
  });
}
`;

  // Write temporary script
  const tempScriptPath = path.join(__dirname, '_extract_temp.ts');
  fs.writeFileSync(tempScriptPath, extractScript);

  // Run with tsx from the SDK root directory
  execSync(
    `cd /Users/koudai/PycharmProjects/lilypad/sdks/typescript && npx tsx ${tempScriptPath}`,
    { stdio: 'inherit' },
  );

  // Clean up
  fs.unlinkSync(tempScriptPath);

  // Verify metadata was created
  const metadataPath = path.join(__dirname, 'lilypad-metadata.json');
  if (!fs.existsSync(metadataPath)) {
    throw new Error('Metadata file was not created');
  }
} catch (error) {
  console.error('❌ Error:', error.message);
  process.exit(1);
}
