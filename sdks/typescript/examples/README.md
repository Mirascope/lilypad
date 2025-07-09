# Lilypad TypeScript SDK Examples

## Getting Started

### Prerequisites

1. Set environment variables:

   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export LILYPAD_API_KEY="your-lilypad-api-key"
   export LILYPAD_PROJECT_ID="your-project-id"
   ```

2. Build the SDK:
   ```bash
   cd /path/to/lilypad/sdks/typescript
   bun install
   bun run build
   ```

## Example 1: Manual Configuration (basic.ts)

Manually calling `lilypad.configure()`:

```bash
# Run with tsx
npx tsx examples/basic.ts

# Or run with bun
bun run examples/basic.ts
```

## Example 2: Auto Instrumentation (basic-auto.ts)

Using `auto_llm: true` to automatically instrument OpenAI:

```bash
# Run with tsx (requiring register.js)
npx tsx --require ../dist/register.js examples/basic-auto.ts

# Or run with node (using transpiled JS)
# First compile TypeScript to JavaScript
npx tsc examples/basic-auto.ts --outDir dist-examples --esModuleInterop --module commonjs --target es2018

# Then run with node
node --require ../dist/register.js dist-examples/basic-auto.js
```

### How register.ts Works

When using `--require ../dist/register.js`:

1. `register.ts` is automatically loaded at program startup
2. `register.ts` performs the following:
   - Reads Lilypad configuration from environment variables
   - Intercepts OpenAI module `require` and `import` calls
   - Automatically wraps OpenAI's `chat.completions.create` method
   - Automatically traces all OpenAI calls

This allows you to trace OpenAI calls without modifying existing code!

## Example 3: Streaming (streaming.ts)

How to handle streaming responses:

```bash
# Run with tsx
npx tsx examples/streaming.ts

# Or run with auto instrumentation
npx tsx --require ../dist/register.js examples/streaming.ts
```

## Troubleshooting

1. If you get `Cannot find module` errors:

   ```bash
   # Rebuild the SDK
   bun run build
   ```

2. Verify environment variables are set:

   ```bash
   echo $OPENAI_API_KEY
   echo $LILYPAD_API_KEY
   ```

3. Check traces in Lilypad dashboard:
   - Open Lilypad dashboard in your browser
   - Select your project
   - Check the "Traces" tab for your requests
