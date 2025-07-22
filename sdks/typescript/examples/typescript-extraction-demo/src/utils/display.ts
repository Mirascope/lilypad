/**
 * Utility to display extracted TypeScript code
 */

import fs from 'fs';
import path from 'path';

interface ExtractedFunction {
  name: string;
  hash: string;
  sourceCode: string;
  signature: string;
  filePath: string;
  startLine: number;
  endLine: number;
}

interface VersioningMetadata {
  version: string;
  buildTime: string;
  functions: Record<string, ExtractedFunction>;
}

export function displayExtractedCode(): void {
  const metadataPath = path.join(process.cwd(), 'lilypad-metadata.json');

  if (!fs.existsSync(metadataPath)) {
    console.log('❌ No metadata file found. Run "npm run extract" first.');
    return;
  }

  try {
    const content = fs.readFileSync(metadataPath, 'utf-8');
    const metadata: VersioningMetadata = JSON.parse(content);

    console.log(`📦 Metadata version: ${metadata.version}`);
    console.log(`🕐 Build time: ${new Date(metadata.buildTime).toLocaleString()}`);
    console.log(`📊 Functions found: ${Object.keys(metadata.functions).length}\n`);

    // Display each function's TypeScript code
    Object.values(metadata.functions).forEach((func, index) => {
      console.log(`━━━ Function ${index + 1}: ${func.name} ━━━`);
      console.log(`📍 Location: ${func.filePath}:${func.startLine}-${func.endLine}`);
      console.log(`🔏 Signature: ${func.signature}`);
      console.log(`\n📝 TypeScript Source Code:\n`);

      // Display code with line numbers
      const lines = func.sourceCode.split('\n');
      lines.forEach((line, i) => {
        const lineNum = String(i + 1).padStart(3, ' ');
        console.log(`${lineNum} │ ${line}`);
      });

      console.log('\n');
    });
  } catch (error) {
    console.error('❌ Error reading metadata:', error);
  }
}

export function checkMetadataExists(): boolean {
  const metadataPath = path.join(process.cwd(), 'lilypad-metadata.json');
  return fs.existsSync(metadataPath);
}
