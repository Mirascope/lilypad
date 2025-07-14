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

### Complete Example: Auto-instrumentation with Custom Tracing

```typescript
import lilypad, { trace } from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

// Configure with auto_llm enabled for automatic OpenAI instrumentation
await lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
  auto_llm: true, // Enable automatic LLM instrumentation
});

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

class QuestionService {
  @trace()
  async answerQuestion(question: string): Promise<string | null> {
    const convertedQuestion = question.toLowerCase().trim();

    // This OpenAI call is automatically traced thanks to auto_llm
    const response = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: `Answer this question: ${convertedQuestion}` }],
    });

    return response.choices[0].message.content;
  }
}

// Usage
const service = new QuestionService();
const response = await service.answerQuestion('What is the capital of France?');
console.log(response);
```

This example demonstrates:

- **Auto-instrumentation**: OpenAI calls are automatically traced with `auto_llm: true`
- **Custom tracing**: Your own functions can be traced with the `@trace()` decorator
- **Complete visibility**: Both your business logic and LLM calls are captured in the same trace

#### Running with Node.js/tsx (Recommended for Auto-instrumentation)

For the best auto-instrumentation experience, use tsx with the --require flag:

```bash
# Install tsx globally or locally
npm install -g tsx
# or
npm install --save-dev tsx

# Set up environment variables
export LILYPAD_API_KEY=your-api-key
export LILYPAD_PROJECT_ID=your-project-id
export OPENAI_API_KEY=your-openai-key

# Run with automatic OpenAI instrumentation
npx tsx --require @lilypad/typescript-sdk/dist/register.js examples/auto-instrumentation-with-trace-node.ts

# Or use the npm script
npm run example:auto-simple:node
```

**Note**: If you encounter decorator issues with tsx, use the `wrapWithTrace` function instead of the `@trace()` decorator, as shown in `examples/auto-instrumentation-simple-node.ts`.

This approach ensures OpenAI calls are automatically instrumented without manual wrapping.

### Option 1: Manual Tracing (if auto_llm is not available)

For environments where auto-instrumentation doesn't work:

```typescript
import lilypad, { wrapOpenAI } from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

await lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
});

// Manually wrap OpenAI for environments like Bun or Deno
const WrappedOpenAI = wrapOpenAI(OpenAI);
const client = new WrappedOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});
```

### Option 2: Automatic Instrumentation with --require flag (Recommended)

When using the `--require` flag, OpenAI is automatically instrumented without any code changes:

```typescript
import lilypad from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

// Configure Lilypad (no auto_llm needed)
await lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
});

// Create OpenAI client normally - NO manual wrapping needed
const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// All OpenAI calls are automatically traced!
const response = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

Run with:

```bash
# With tsx (TypeScript)
npx tsx --require @lilypad/typescript-sdk/dist/register.js your-script.ts

# With node (JavaScript)
node --require @lilypad/typescript-sdk/dist/register.js your-script.js
```

This method automatically instruments all OpenAI calls when the module is loaded.

### Option 3: Automatic Instrumentation with ESM Loader

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

## Trace Decorator

The Lilypad SDK provides a `@trace` decorator for instrumenting your own functions with distributed tracing.

### Dual Decorator Support

The SDK supports both legacy decorators (`experimentalDecorators: true`) and Stage-3 decorators, with automatic runtime detection:

- **Node.js with TypeScript**: Uses legacy decorators by default
- **Bun**: Uses Stage-3 decorators natively
- **Explicit imports**: Force a specific version with `/legacy` or `/modern` paths

```typescript
// Auto-detect (recommended)
import { trace } from '@lilypad/typescript-sdk';

// Force legacy decorators
import { trace } from '@lilypad/typescript-sdk/legacy';

// Force Stage-3 decorators
import { trace } from '@lilypad/typescript-sdk/modern';
```

### Basic Usage

```typescript
import { trace } from '@lilypad/typescript-sdk';

class DataService {
  // Note: @trace decorator always returns a Promise, even for sync methods
  @trace()
  processData(input: string): Promise<string> {
    return input.toUpperCase();
  }

  @trace({ name: 'custom-span-name' })
  async fetchData(id: string): Promise<any> {
    const response = await fetch(`/api/data/${id}`);
    return response.json();
  }
}

// Usage
const service = new DataService();
// Even though processData looks synchronous, it returns a Promise
const result = await service.processData('hello'); // Returns: "HELLO"
```

**Important**: The `@trace` decorator always wraps methods to return a Promise for tracing purposes. If you need truly synchronous behavior, use the `wrapWithTrace` function instead.

### TSX Compatibility

#### Option 1: Using @trace with Custom Config (Recommended)

To use `@trace` decorators with tsx, use the custom TypeScript configuration:

```bash
# Run with custom tsconfig that enables decorators
npx tsx --tsconfig tsconfig.tsx.json your-file.ts

# With auto-instrumentation
npx tsx --tsconfig tsconfig.tsx.json --require ./dist/register.js your-file.ts
```

Example:

```typescript
import { trace } from '@lilypad/typescript-sdk';

class Service {
  @trace()
  async processData(input: string): Promise<string> {
    return input.toUpperCase();
  }

  @trace({ mode: 'wrap', tags: ['important'] })
  async analyzeData(data: any): Promise<any> {
    // Returns a Trace object for annotations
    return { analysis: 'complete' };
  }
}
```

#### Option 2: Using wrapWithTrace (Alternative)

If you encounter issues with decorators, use `wrapWithTrace` instead:

```typescript
import { wrapWithTrace } from '@lilypad/typescript-sdk';

class DataService {
  // Use wrapWithTrace for tsx compatibility
  processData = wrapWithTrace(
    async (input: string): Promise<string> => {
      return input.toUpperCase();
    },
    { name: 'processData' },
  );

  fetchData = wrapWithTrace(
    async (id: string): Promise<any> => {
      const response = await fetch(`/api/data/${id}`);
      return response.json();
    },
    { name: 'fetchData', tags: ['api', 'fetch'] },
  );
}
```

This approach works with both Bun and tsx without configuration issues.

### Wrap Mode

The `mode: 'wrap'` option returns a `Trace` object instead of the raw result, enabling post-execution operations:

```typescript
import { trace, Trace, AsyncTrace } from '@lilypad/typescript-sdk';

class AnalyticsService {
  @trace({ mode: 'wrap' })
  analyzeData(data: any): { score: number; category: string } {
    // Your analysis logic
    return { score: 0.85, category: 'positive' };
  }
}

// Usage
const service = new AnalyticsService();
const result = service.analyzeData(someData);

// result is a Trace<T> object, not the raw result
console.log(result.response); // Access the actual result: { score: 0.85, category: 'positive' }

// Add tags
result.tag('production', 'analytics');

// Assign to team members
result.assign('reviewer@example.com', 'qa@example.com');
```

### Async Functions with Wrap Mode

For async functions, wrap mode returns an `AsyncTrace` object:

```typescript
class MLService {
  @trace({ mode: 'wrap', tags: ['ml', 'inference'] })
  async predict(input: any): Promise<{ prediction: string; confidence: number }> {
    // Async ML inference
    return { prediction: 'category_a', confidence: 0.92 };
  }
}

const mlService = new MLService();
const traceResult = await mlService.predict(inputData);

// Access the response
const prediction = traceResult.response;

// Add tags based on confidence
await traceResult.tag(
  prediction.confidence > 0.9 ? 'high-confidence' : 'low-confidence',
  'ml-prediction',
);
```

### Trace Options

```typescript
interface TraceOptions {
  name?: string; // Custom span name (default: class.method)
  mode?: 'wrap' | null; // Return mode: 'wrap' returns Trace object, null returns raw result
  tags?: string[]; // Tags to attach to the span
  attributes?: Record<string, any>; // Additional span attributes
}
```

### Annotation Structure

```typescript
interface Annotation {
  data?: Record<string, any> | null; // Custom data to attach
  label?: 'pass' | 'fail' | null; // Evaluation label
  reasoning?: string | null; // Explanation for the evaluation
  type?: 'manual' | 'automatic' | null; // How the annotation was created
}
```

## Function Versioning

The TypeScript SDK supports automatic function versioning, allowing you to track code changes and manage different versions of your functions.

### Basic Usage

```typescript
class DataService {
  @trace({ versioning: 'automatic' })
  async processData(input: string): Promise<string> {
    // Function implementation
    return input.toUpperCase();
  }
}

const service = new DataService();

// Execute normally
const result = await service.processData('hello');

// Access versioning methods
const versions = await service.processData.versions(); // List all versions
const v1 = service.processData.version(1); // Get specific version
await service.processData.deploy(1); // Deploy a version
const remote = await service.processData.remote('input'); // Execute deployed version
```

### Versioning Methods

Every versioned function gets these methods:

- `fn.version(n)` - Execute a specific version
- `fn.versions()` - List all available versions
- `fn.deploy(n)` - Deploy a specific version
- `fn.remote(...args)` - Execute the deployed version

### Important Notes

- **Decorators only work on class methods** in TypeScript
- For standalone functions, use `wrapWithTrace()` with versioning option
- Function code is automatically captured and hashed for versioning
- Versions are tracked in the Lilypad backend

### Example with Wrap Mode

```typescript
@trace({ versioning: 'automatic', mode: 'wrap' })
async analyzeData(data: any): Promise<{ score: number }> {
  return { score: Math.random() };
}

// Returns AsyncTrace with versioning methods
const result = await service.analyzeData(data);
console.log(result.response); // { score: 0.85 }
await result.tag('analyzed');
```

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
# Basic example
bun run example:basic

# Auto-instrumentation with custom tracing (Bun - manual wrapping)
bun run example:auto-with-trace

# Auto-instrumentation with custom tracing (Node.js/tsx - automatic)
npm run example:auto-require:node
# or directly:
npx tsx --require ./dist/register.js examples/auto-instrumentation-require-only.ts

# Alternative with wrapWithTrace function (avoids decorator issues)
npm run example:auto-simple:node

# Example with @trace decorators

# Option 1: Use Bun (native decorator support)
npm run example:auto-decorator:bun

# Option 2: Compile with tsc then run with Node.js (recommended for --require)
npm run example:auto-decorator:compile  # Compile TypeScript
npm run example:auto-decorator:compiled  # Run compiled JS with --require

# Option 3: Try tsx with explicit tsconfig (may have issues)
npm run example:auto-decorator:node

# Trace decorator with wrap mode
bun run example:trace-wrap

# Dual decorator support example
bun run example:dual-decorator

# Or run directly with environment variables
OPENAI_API_KEY=your-key LILYPAD_API_KEY=your-key LILYPAD_PROJECT_ID=your-project-id bun run examples/auto-instrumentation-with-trace.ts
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
