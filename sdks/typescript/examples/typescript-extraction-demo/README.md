# TypeScript Extraction Demo

This example demonstrates how to use Lilypad SDK's TypeScript extraction feature to capture original TypeScript code at build time.

## What This Demo Shows

1. **TypeScript Code Extraction**: Original TypeScript code (with types) is extracted during build
2. **Multiple Function Examples**: Various TypeScript features that are preserved
3. **Versioning Integration**: How extracted code works with Lilypad's versioning system

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Extract TypeScript Code

```bash
npm run extract
```

This creates `lilypad-metadata.json` containing the TypeScript source code.

### 3. Run the Demo

```bash
npm run dev
```

## What Happens

1. **Build Time**: The `lilypad-extract` command scans TypeScript files and extracts functions marked with `versioning: 'automatic'`

2. **Metadata File**: Creates `lilypad-metadata.json` with:
   - Original TypeScript source code
   - Function signatures with types
   - File locations
   - Dependencies

3. **Runtime**: The SDK loads this metadata and uses TypeScript code instead of JavaScript

## Try It Yourself

### 1. Watch Mode

Run extraction in watch mode to see real-time updates:

```bash
npm run extract:watch
```

### 2. Modify Functions

Edit `src/services/business-logic.ts` and see the metadata update automatically.

### 3. View Extracted Code

Check `lilypad-metadata.json` to see the extracted TypeScript:

```bash
cat lilypad-metadata.json | jq '.functions[].sourceCode' -r
```

## Function Examples

The demo includes functions showcasing:

- **Type Annotations**: Interfaces, types, and generics
- **Async Functions**: Promise return types
- **JSDoc Comments**: Documentation preservation
- **Complex Parameters**: Nested objects and union types
- **Generic Functions**: Type parameters
- **Named and Arrow Functions**: Different function styles

## Build Integration

### Manual Extraction

```bash
npm run extract
npm run build
```

### Automatic with Build

```json
{
  "scripts": {
    "prebuild": "npm run extract",
    "build": "tsc"
  }
}
```

### With Bundlers

See the main user-project example for Vite and Webpack integration.

## Files Generated

- `lilypad-metadata.json`: Contains extracted TypeScript code
- `dist/`: Compiled JavaScript (after `npm run build`)

## Deployment

Remember to include `lilypad-metadata.json` when deploying your application!

## Troubleshooting

### No Functions Found

Make sure functions have `versioning: 'automatic'`:

```typescript
// ✅ Correct
const myFunc = trace(async () => {}, { versioning: 'automatic' });

// ❌ Wrong
const myFunc = trace(async () => {});
```

### TypeScript Not Showing

1. Check that `lilypad-metadata.json` exists
2. Ensure it's in the same directory as your app
3. Verify the SDK can find it at runtime
