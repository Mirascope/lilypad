/**
 * Simple extraction script for the demo
 * This runs the TypeScript extractor directly without compilation
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔍 Extracting TypeScript code...');

try {
  // Run the TypeScript extractor using tsx
  const command = `cd ../.. && tsx scripts/extract-versioning-metadata.ts`;
  execSync(command, { stdio: 'inherit' });

  // Copy the generated metadata to our demo directory
  const sourceMetadata = path.join(__dirname, '../../dist/versioning-metadata.json');
  const targetMetadata = path.join(__dirname, 'lilypad-metadata.json');

  if (fs.existsSync(sourceMetadata)) {
    const metadata = JSON.parse(fs.readFileSync(sourceMetadata, 'utf-8'));

    // Filter only functions from this demo
    const demoFunctions = {};
    Object.entries(metadata.functions).forEach(([hash, func]) => {
      if (func.filePath.includes('typescript-extraction-demo')) {
        demoFunctions[hash] = func;
      }
    });

    const demoMetadata = {
      ...metadata,
      functions: demoFunctions,
    };

    fs.writeFileSync(targetMetadata, JSON.stringify(demoMetadata, null, 2));

    const functionCount = Object.keys(demoFunctions).length;
    console.log(`✅ Extracted ${functionCount} versioned functions from this demo`);

    if (functionCount > 0) {
      console.log('\n📋 Functions:');
      Object.values(demoFunctions).forEach((fn) => {
        console.log(`   - ${fn.name} (${fn.filePath}:${fn.startLine})`);
      });
    }
  } else {
    throw new Error('Metadata file not generated');
  }
} catch (error) {
  console.error('❌ Error:', error.message);
  process.exit(1);
}
