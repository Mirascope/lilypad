#!/bin/bash

# TypeScript Extraction Demo Runner
# This script demonstrates the complete workflow

set -e

echo "🚀 TypeScript Extraction Demo"
echo "============================"
echo ""

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf dist lilypad-metadata.json
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install --silent
echo ""

# Extract TypeScript code
echo "🔍 Extracting TypeScript code..."
npm run extract
echo ""

# Show extracted functions
echo "📊 Extracted functions:"
if [ -f lilypad-metadata.json ]; then
  node -e "
    const fs = require('fs');
    const metadata = JSON.parse(fs.readFileSync('lilypad-metadata.json'));
    const functions = Object.values(metadata.functions);
    console.log('   Found ' + functions.length + ' versioned functions:');
    functions.forEach(f => {
      console.log('   - ' + f.name + ' (' + f.filePath + ':' + f.startLine + ')');
    });
  "
else
  echo "   ❌ No metadata file found!"
  exit 1
fi
echo ""

# Run the demo
echo "▶️  Running demo..."
echo "===================="
npm run dev

echo ""
echo "✅ Demo complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Try watch mode: npm run extract:watch"
echo "   2. Modify src/services/business-logic.ts"
echo "   3. Check lilypad-metadata.json for extracted TypeScript"