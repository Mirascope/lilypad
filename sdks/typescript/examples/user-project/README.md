# Lilypad TypeScript SDK - User Project Example

This example demonstrates how to use the Lilypad TypeScript SDK with automatic TypeScript code extraction in your own project.

## Setup

1. Install dependencies:

```bash
npm install
```

2. Configure Lilypad credentials:

```bash
export LILYPAD_API_KEY="your-api-key"
export LILYPAD_PROJECT_ID="your-project-id"
```

## Build Methods

### Method 1: CLI Tool (Recommended)

Use the `lilypad-extract` CLI tool in your build process:

```bash
# Extract metadata once
npm run extract

# Extract and watch for changes
npm run extract:watch

# Build with extraction
npm run build
```

### Method 2: Vite Plugin

The project includes a Vite configuration that automatically extracts TypeScript metadata:

```bash
# Development with auto-extraction
npm run dev

# Production build
npm run build
```

### Method 3: Webpack Plugin

Alternative webpack configuration:

```bash
# Build with webpack
npm run build:webpack
```

## How It Works

1. **TypeScript Code Extraction**: During the build process, the Lilypad tools scan your TypeScript files for functions marked with `versioning: 'automatic'`.

2. **Metadata Generation**: The original TypeScript source code is extracted and saved to `lilypad-metadata.json`.

3. **Runtime Usage**: When your application runs, the SDK loads this metadata and sends the TypeScript code (not JavaScript) to the Lilypad server.

## What Gets Extracted

Look at `src/index.ts` for examples of versioned functions:

- `calculateOrderTotal`: Async function with complex return types
- `filterProducts`: Generic function with type parameters
- `processInventory`: Function with complex parameter types

After building, check `lilypad-metadata.json` to see the extracted TypeScript code.

## Integration Options

### 1. NPM Scripts (Simple)

Add to your `package.json`:

```json
{
  "scripts": {
    "prebuild": "lilypad-extract",
    "build": "your-build-command"
  }
}
```

### 2. Vite Plugin (Automatic)

```ts
// vite.config.ts
import { lilypadPlugin } from '@lilypad/typescript-sdk/vite';

export default {
  plugins: [lilypadPlugin()],
};
```

### 3. Webpack Plugin (Automatic)

```js
// webpack.config.js
const { LilypadWebpackPlugin } = require('@lilypad/typescript-sdk/webpack');

module.exports = {
  plugins: [new LilypadWebpackPlugin()],
};
```

### 4. Custom Build Script

```ts
// build.ts
import { TypeScriptExtractor } from '@lilypad/typescript-sdk/extractor';

const extractor = new TypeScriptExtractor('./');
const metadata = extractor.extract();
// Save metadata...
```

## Deployment

Include `lilypad-metadata.json` in your deployment:

- It should be in the same directory as your built JavaScript files
- The SDK will automatically load it at runtime
- Without this file, the SDK falls back to JavaScript code
