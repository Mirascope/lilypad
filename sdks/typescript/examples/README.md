# Lilypad TypeScript SDK Examples

This directory contains examples demonstrating how to use the Lilypad TypeScript SDK.

## Prerequisites

1. Set environment variables:

   ```bash
   export LILYPAD_API_KEY="your-lilypad-api-key"
   export LILYPAD_PROJECT_ID="your-project-id"
   export OPENAI_API_KEY="your-openai-api-key"  # Optional for OpenAI examples
   ```

2. Build the SDK:
   ```bash
   bun install
   bun run build
   ```

## Core Examples

### 1. Basic Usage (`basic.ts`)

Simple example showing basic SDK configuration and OpenAI integration.

```bash
# Run with Bun
bun run examples/basic.ts

# Run with Node.js/tsx
npx tsx examples/basic.ts
```

### 2. Comprehensive Example (`comprehensive.ts`)

Complete example demonstrating all major features:

- trace() function for method instrumentation
- OpenAI integration
- Wrap mode with annotations
- Both decorator and functional approaches

```bash
# With Bun (native decorator support)
bun run examples/comprehensive.ts

# With tsx (using custom tsconfig)
npx tsx --tsconfig tsconfig.tsx.json examples/comprehensive.ts

# With auto-instrumentation
npx tsx --require ./dist/register.js examples/comprehensive.ts
```

### 3. Streaming (`streaming.ts`)

Shows how to handle streaming responses from OpenAI with proper span lifecycle management.

```bash
# Basic streaming
bun run examples/streaming.ts

# With auto-instrumentation
npx tsx --require ./dist/register.js examples/streaming.ts
```

### 4. Trace Wrap Mode (`trace-wrap-mode.ts`)

Advanced tracing features using wrap mode:

- Post-execution annotations
- Tagging spans
- Assigning traces to team members

```bash
bun run examples/trace-wrap-mode.ts
```

## Running Examples

### Option 1: Using Bun (Recommended)

Bun has native support for TypeScript and decorators:

```bash
bun run examples/[example-name].ts
```

### Option 2: Using tsx

For running with tsx:

```bash
npx tsx examples/[example-name].ts
```

### Option 3: With Auto-instrumentation

To automatically trace OpenAI calls without manual wrapping:

```bash
npx tsx --require ./dist/register.js examples/[example-name].ts
```

## Key Features Demonstrated

1. **Basic Tracing**: Manual span creation and metadata tracking
2. **Function Tracing**: Using trace() function for method instrumentation
3. **Wrap Mode**: Getting trace objects for post-execution operations
4. **Auto-instrumentation**: Automatic OpenAI call tracing with --require
5. **Streaming**: Handling streaming responses with proper cleanup
6. **Annotations**: Adding labels and metadata to traces after execution

## Troubleshooting

1. **TypeScript errors**: Ensure you've built the SDK with `bun run build` first
2. **OpenAI not traced**: Use `--require ./dist/register.js` for auto-instrumentation
3. **Module not found**: Run `bun run build` first
4. **No traces appearing**: Check environment variables and wait for batch export

## Viewing Traces

After running an example, look for output like:

```
[Lilypad] View trace: https://app.lilypad.so/projects/xxx/traces/yyy
```

Click the link to view your trace in the Lilypad dashboard.
