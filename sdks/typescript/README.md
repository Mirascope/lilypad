# Lilypad TypeScript SDK

TypeScript SDK for Lilypad - LLM observability and monitoring platform.

## Installation

```bash
npm install @lilypad/typescript-sdk
# or
yarn add @lilypad/typescript-sdk
# or
bun add @lilypad/typescript-sdk
```

## Quick Start

### Option 1: Manual Tracing

```typescript
import lilypad from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

// Configure the SDK
await lilypad.configure({
  apiKey: 'your-api-key',
  projectId: 'your-project-id',
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Manually trace OpenAI calls
const response = await lilypad.traceOpenAICompletion(
  {
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Hello, how are you?' }],
  },
  () =>
    openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: 'Hello, how are you?' }],
    }),
);
```

### Option 2: Automatic Instrumentation with auto_llm

Enable automatic instrumentation in your code without requiring a command-line flag:

```typescript
import lilypad from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

// Configure with auto_llm enabled
await lilypad.configure({
  apiKey: 'your-api-key',
  projectId: 'your-project-id',
  auto_llm: true, // Enable automatic LLM instrumentation
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// OpenAI calls are automatically traced!
const response = await openai.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hello, how are you?' }],
});
```

### Option 3: Automatic Instrumentation with --require flag (CommonJS)

```bash
# Run with tsx
npx tsx --require @lilypad/typescript-sdk/dist/register.cjs your-script.ts

# Or with node
node --require @lilypad/typescript-sdk/dist/register.cjs your-script.js
```

This method automatically instruments all OpenAI calls when the module is loaded, without requiring `auto_llm: true` in your configuration.

### Option 4: Automatic Instrumentation with ESM Loader

For ESM modules, use the loader hooks:

```bash
# Node.js >= 18.19
node --import @lilypad/typescript-sdk/dist/register-esm-loader.mjs your-app.mjs

# Node.js < 18.19
node --loader @lilypad/typescript-sdk/dist/register-esm-loader.mjs your-app.mjs

# With tsx for TypeScript ESM
tsx --import @lilypad/typescript-sdk/dist/register-esm-loader.mjs your-app.ts
```

This provides full ESM support for auto-instrumentation.

## Configuration Options

```typescript
interface LilypadConfig {
  apiKey: string; // Required: Your Lilypad API key
  projectId: string; // Required: Your Lilypad project ID
  baseUrl?: string; // Optional: API base URL (defaults to Lilypad hosted service)
  remoteClientUrl?: string; // Optional: URL for viewing traces
  logLevel?: 'debug' | 'info' | 'warn' | 'error'; // Optional: Logging level (default: 'info')
  serviceName?: string; // Optional: Service name for telemetry (default: 'lilypad-node-app')
  auto_llm?: boolean; // Optional: Automatically instrument LLM libraries (default: false)
  propagator?: 'tracecontext' | 'b3' | 'b3multi' | 'jaeger' | 'composite'; // Optional: Trace propagation format
  preserveExistingPropagator?: boolean; // Optional: Preserve existing propagator (default: false)
  batchProcessorOptions?: {
    // Optional: Span export batching options
    scheduledDelayMillis?: number; // Delay between exports (default: 5000)
    maxQueueSize?: number; // Max queue size (default: 2048)
    maxExportBatchSize?: number; // Max batch size (default: 512)
    exportTimeoutMillis?: number; // Export timeout (default: 30000)
  };
}
```

## OpenAI Integration

### Automatic Instrumentation

#### Node.js

For Node.js applications, automatic instrumentation works by using the `--require` flag:

```bash
# Using tsx
npx tsx --require @lilypad/typescript-sdk/dist/register.js your-app.ts

# Using Node.js directly
node --require @lilypad/typescript-sdk/dist/register.js your-app.js
```

This automatically traces all OpenAI calls without code changes.

#### Bun

⚠️ **Note**: Bun does not support Node.js module hooks (`Module._load`), so automatic instrumentation via `--require` does not work. You must use manual instrumentation:

```typescript
import { configure, wrapOpenAI } from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

// Configure Lilypad
await configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID,
});

// Manually wrap OpenAI
const WrappedOpenAI = wrapOpenAI(OpenAI);
const openai = new WrappedOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Use OpenAI as normal - calls will be traced
const response = await openai.chat.completions.create({
  model: 'gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

#### Deno

Similar to Bun, Deno requires manual instrumentation. Use the `wrapOpenAI` function as shown above.

### Standard Completion

```typescript
const response = await openai.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [
    { role: 'system', content: 'You are a helpful assistant.' },
    { role: 'user', content: 'What is the capital of France?' },
  ],
  temperature: 0.7,
  max_tokens: 100,
});
```

### Streaming Responses

```typescript
const stream = await openai.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

Both standard and streaming responses are fully traced with:

- Request parameters (model, temperature, max_tokens, etc.)
- Messages content
- Response content and usage statistics
- Timing information
- Error tracking

## Shutdown

The SDK automatically handles graceful shutdown on process termination (SIGTERM, SIGINT, and normal exit) to ensure all spans are flushed. You can also manually trigger shutdown:

```typescript
// Manual shutdown
await lilypad.shutdown();

// Disable automatic shutdown handlers if needed
process.env.LILYPAD_DISABLE_AUTO_SHUTDOWN = 'true';

// Or handle shutdown explicitly in your application:
process.on('beforeExit', async () => {
  await lilypad.shutdown();
});
```

**Important for serverless/Lambda environments**: Call `shutdown()` explicitly before your function completes to ensure all data is sent:

```typescript
export const handler = async (event) => {
  try {
    // Your function logic here
    const result = await processEvent(event);
    return result;
  } finally {
    // Ensure spans are flushed before Lambda freezes
    await lilypad.shutdown();
  }
};
```

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/Mirascope/lilypad.git
cd lilypad/sdks/typescript

# Install dependencies
bun install

# Build the SDK
bun run build

# Run tests
bun run test

# Run linting
bun run lint

# Type check
bun run typecheck
```

### Running Examples

```bash
# Manual tracing example
bun run example:basic

# Automatic instrumentation example
bun run example:auto

# Or run directly with environment variables
OPENAI_API_KEY=your-key LILYPAD_API_KEY=your-key LILYPAD_PROJECT_ID=your-project-id bun run example:auto
```

## Requirements

- Node.js >= 18.0.0
- OpenAI SDK ^4.0.0 (optional, for auto_llm feature)

## License

MIT

## Support

- [Documentation](https://docs.lilypad.so)
- [GitHub Issues](https://github.com/Mirascope/lilypad/issues)
- [Discord Community](https://discord.gg/lilypad)
