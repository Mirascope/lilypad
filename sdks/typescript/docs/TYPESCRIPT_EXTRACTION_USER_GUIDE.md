# TypeScript Code Extraction - User Guide

This guide explains how to set up TypeScript code extraction in your project when using the Lilypad TypeScript SDK.

## Why TypeScript Extraction?

When you use versioned functions with Lilypad, the SDK needs to capture your function code. By default, this happens at runtime using JavaScript. However, with TypeScript extraction:

- Your original TypeScript code (with types) is shown in the Lilypad UI
- Better readability and debugging
- Preserves type annotations, generics, and interfaces
- Automatically captures all dependencies (functions, types, constants) used by your traced functions
- Creates self-contained code blocks that include everything needed to run independently

## Quick Start

### 1. Install the SDK

```bash
npm install @lilypad/typescript-sdk
# or
yarn add @lilypad/typescript-sdk
# or
bun add @lilypad/typescript-sdk
```

### 2. Choose Your Build Tool

#### Option A: Using CLI (Works with any build tool)

Add to your `package.json`:

```json
{
  "scripts": {
    "prebuild": "lilypad-extract",
    "build": "tsc" // or your build command
  }
}
```

#### Option B: Using Vite

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import { lilypadPlugin } from '@lilypad/typescript-sdk/vite';

export default defineConfig({
  plugins: [lilypadPlugin()],
});
```

#### Option C: Using Webpack

```js
// webpack.config.js
const { LilypadWebpackPlugin } = require('@lilypad/typescript-sdk/webpack');

module.exports = {
  plugins: [new LilypadWebpackPlugin()],
};
```

### 3. Mark Functions for Versioning

```typescript
import { trace } from '@lilypad/typescript-sdk';

// This function's TypeScript code will be extracted
export const calculatePrice = trace(
  async (items: CartItem[]): Promise<number> => {
    return items.reduce((sum, item) => sum + item.price, 0);
  },
  { versioning: 'automatic' }, // ← Required for extraction
);
```

### 4. Build Your Project

```bash
npm run build
```

This creates `lilypad-metadata.json` containing your TypeScript source code.

## CLI Options

The `lilypad-extract` command supports these options:

```bash
lilypad-extract [options]

Options:
  -p, --project <path>     Path to tsconfig.json (default: ./tsconfig.json)
  -o, --output <path>      Output path for metadata (default: ./lilypad-metadata.json)
  --include <patterns...>  Glob patterns to include (default: src/**/*.ts)
  -w, --watch             Watch mode for development
  --verbose               Verbose output
```

### Examples:

```bash
# Basic usage
lilypad-extract

# Custom TypeScript config
lilypad-extract --project tsconfig.app.json

# Watch mode during development
lilypad-extract --watch

# Custom output location
lilypad-extract --output dist/lilypad-metadata.json

# Include test files
lilypad-extract --include "src/**/*.ts" "tests/**/*.ts"
```

## Plugin Configuration

### Vite Plugin Options

```ts
lilypadPlugin({
  tsConfig: './tsconfig.json', // Path to TypeScript config
  output: 'lilypad-metadata.json', // Output filename
  include: ['src/**/*.ts'], // File patterns to scan
  verbose: false, // Enable logging
});
```

### Webpack Plugin Options

```js
new LilypadWebpackPlugin({
  tsConfig: './tsconfig.json',
  output: 'lilypad-metadata.json',
  include: ['src/**/*.ts', 'src/**/*.tsx'],
  verbose: false,
});
```

## Deployment

**Important**: Include `lilypad-metadata.json` in your deployment!

### Docker Example

```dockerfile
# Build stage
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/lilypad-metadata.json ./  # ← Don't forget this!
COPY package*.json ./
RUN npm ci --production
CMD ["node", "dist/index.js"]
```

### Vercel/Netlify

The metadata file is automatically included in the build output when using our plugins.

## Troubleshooting

### "TypeScript source not found"

1. Check that `lilypad-metadata.json` exists after building
2. Ensure the file is deployed with your application
3. Verify functions have `versioning: 'automatic'`

### "No versioned functions found"

Make sure your functions use the correct syntax:

```typescript
// ✅ Correct
const myFunc = trace(async () => {}, { versioning: 'automatic' });

// ❌ Wrong - missing versioning option
const myFunc = trace(async () => {});

// ❌ Wrong - versioning not set to 'automatic'
const myFunc = trace(async () => {}, { versioning: null });
```

### Build Performance

For large projects, you can optimize extraction:

```bash
# Only scan specific directories
lilypad-extract --include "src/api/**/*.ts"

# Exclude test files
lilypad-extract --include "src/**/*.ts" "!src/**/*.test.ts"
```

## Advanced Usage

### Custom Build Integration

```ts
// build.ts
import { TypeScriptExtractor } from '@lilypad/typescript-sdk/extractor';
import * as fs from 'fs';

async function build() {
  // Extract TypeScript metadata
  const extractor = new TypeScriptExtractor('./');
  const metadata = extractor.extract();

  // Save metadata
  fs.writeFileSync('lilypad-metadata.json', JSON.stringify(metadata, null, 2));

  // Continue with your build...
}
```

### Runtime Metadata Loading

The SDK automatically loads metadata, but you can verify:

```typescript
import { metadataLoader } from '@lilypad/typescript-sdk/versioning';

// Check if metadata is available
if (metadataLoader.hasMetadata()) {
  console.log('TypeScript extraction is working!');
}
```

## Best Practices

1. **Include in CI/CD**: Always run extraction in your build pipeline
2. **Git Ignore**: Add `lilypad-metadata.json` to `.gitignore` (it's generated)
3. **Watch Mode**: Use `--watch` during development for instant updates
4. **Optimize Patterns**: Only scan directories with versioned functions

## Dependency Extraction

The TypeScript SDK now captures not just your function code, but all its dependencies, creating self-contained code blocks similar to Python's Closure functionality.

### What Gets Captured?

When you trace a function with `versioning: 'automatic'`, the SDK automatically captures:

1. **The main function** - Your traced function with all TypeScript types
2. **Called functions** - Any functions called within your traced function
3. **Type definitions** - Interfaces, type aliases, and enums used
4. **Constants and variables** - Any external values referenced
5. **Import dependencies** - Follows relative imports to capture external functions

### Example: Complete Dependency Capture

```typescript
// types.ts
export interface Product {
  id: string;
  name: string;
  price: number;
}

export interface User {
  name: string;
  premium: boolean;
}

// helpers.ts
export const TAX_RATE = 0.08;
export const PREMIUM_DISCOUNT = 0.15;

export function calculateDiscount(user: User): number {
  return user.premium ? PREMIUM_DISCOUNT : 0;
}

export function formatCurrency(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

// main.ts
import { trace } from '@lilypad/typescript-sdk';
import { Product, User } from './types';
import { TAX_RATE, calculateDiscount, formatCurrency } from './helpers';

function calculateTax(subtotal: number): number {
  return subtotal * TAX_RATE;
}

// This traced function uses multiple dependencies
const processCheckout = trace(
  function (user: User, products: Product[]): string {
    const subtotal = products.reduce((sum, p) => sum + p.price, 0);
    const discount = calculateDiscount(user);
    const discountAmount = subtotal * discount;
    const afterDiscount = subtotal - discountAmount;
    const tax = calculateTax(afterDiscount);
    const total = afterDiscount + tax;

    return `Total: ${formatCurrency(total)}`;
  },
  { versioning: 'automatic' },
);
```

### What Appears in Lilypad UI

The captured self-contained code includes everything:

```typescript
// External imports
// (none in this case - all code is captured)

// Type dependencies
interface Product {
  id: string;
  name: string;
  price: number;
}

interface User {
  name: string;
  premium: boolean;
}

// Variable and class dependencies
const TAX_RATE = 0.08;
const PREMIUM_DISCOUNT = 0.15;

// Function dependencies
function calculateDiscount(user: User): number {
  return user.premium ? PREMIUM_DISCOUNT : 0;
}

function formatCurrency(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

function calculateTax(subtotal: number): number {
  return subtotal * TAX_RATE;
}

// Main function
function(user: User, products: Product[]): string {
  const subtotal = products.reduce((sum, p) => sum + p.price, 0);
  const discount = calculateDiscount(user);
  const discountAmount = subtotal * discount;
  const afterDiscount = subtotal - discountAmount;
  const tax = calculateTax(afterDiscount);
  const total = afterDiscount + tax;

  return `Total: ${formatCurrency(total)}`;
}
```

### Benefits

1. **Complete Context**: See all the code needed to understand the function
2. **Self-Contained**: The captured code can run independently
3. **Cross-File Dependencies**: Automatically follows imports from other files
4. **Type Safety**: All TypeScript types are preserved
5. **No Manual Work**: Everything is captured automatically

## Example Project Structure

```
my-app/
├── src/
│   ├── index.ts
│   ├── api/
│   │   └── handlers.ts      # Contains versioned functions
│   └── utils/
│       └── helpers.ts       # Dependencies get captured too!
├── package.json
├── tsconfig.json
├── vite.config.ts           # With lilypadPlugin
└── lilypad-metadata.json    # Generated (git ignored)
```

## Need Help?

- Check the [example project](../examples/user-project/) for a complete setup
- Report issues at: https://github.com/Mirascope/lilypad/issues
- Join our Discord: [discord.gg/lilypad](https://discord.gg/lilypad)
