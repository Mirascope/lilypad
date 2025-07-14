# Lilypad TypeScript SDK Examples

This directory contains examples demonstrating how to use the Lilypad TypeScript SDK.

## Important: TypeScript Decorators

**TypeScript decorators (`@trace`) only work on class methods, not standalone functions.**

- ✅ Use `@trace()` on class methods
- ❌ Cannot use `@trace()` on standalone functions
- ✅ Use `wrapWithTrace()` for standalone functions

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

### 2. Trace Decorator Examples (`trace-decorator-examples.ts`, `trace-decorator-class-methods.ts`)

Comprehensive examples showing how to use `@trace` decorator on class methods:

- Basic class methods with `@trace()`
- Async methods with error handling
- Wrap mode for post-processing
- Versioning with decorators
- Custom tags and attributes

```bash
# Run decorator examples
bun run examples/trace-decorator-examples.ts
bun run examples/trace-decorator-class-methods.ts
```

### 3. Comprehensive Example (`comprehensive.ts`)

Complete example demonstrating all major features:

- @trace decorator (Bun) and wrapWithTrace (tsx)
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

### Option 2: Using tsx with Decorators

For decorator support in tsx, use the custom tsconfig:

```bash
npx tsx --tsconfig tsconfig.tsx.json examples/[example-name].ts
```

### Option 3: With Auto-instrumentation

To automatically trace OpenAI calls without manual wrapping:

```bash
npx tsx --require ./dist/register.js examples/[example-name].ts
```

## Key Features Demonstrated

1. **Basic Tracing**: Manual span creation and metadata tracking
2. **Decorators**: Using @trace decorator for method instrumentation
3. **Wrap Mode**: Getting trace objects for post-execution operations
4. **Auto-instrumentation**: Automatic OpenAI call tracing with --require
5. **Streaming**: Handling streaming responses with proper cleanup
6. **Annotations**: Adding labels and metadata to traces after execution

## Troubleshooting

1. **Decorator errors with tsx**: Use `--tsconfig tsconfig.tsx.json` or switch to `wrapWithTrace`
2. **OpenAI not traced**: Use `--require ./dist/register.js` for auto-instrumentation
3. **Module not found**: Run `bun run build` first
4. **No traces appearing**: Check environment variables and wait for batch export

## Viewing Traces

After running an example, look for output like:

```
[Lilypad] View trace: https://app.lilypad.so/projects/xxx/traces/yyy
```

Click the link to view your trace in the Lilypad dashboard.
