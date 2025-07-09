# Lilypad TypeScript SDK Examples

This directory contains examples demonstrating how to use the Lilypad TypeScript SDK.

## Prerequisites

1. Set environment variables:

   ```bash
   export LILYPAD_API_KEY="your-lilypad-api-key"
   export LILYPAD_PROJECT_ID="your-project-id"
   export OPENAI_API_KEY="your-openai-api-key"  # For OpenAI examples

   # Optional: Use staging environment
   export LILYPAD_BASE_URL="https://lilypad-staging.up.railway.app/v0"
   ```

2. Build the SDK:
   ```bash
   bun install
   bun run build
   ```

## Available Examples

### 1. Basic Usage (`basic.ts`)

Basic example showing manual span creation and metadata tracking.

```bash
npx tsx examples/basic.ts
```

### 2. Span with Auto-instrumented LLM (`span-with-auto-llm.ts`)

Demonstrates how to combine manual spans with auto-instrumented OpenAI calls.

```bash
# REQUIRED: Use --require flag for auto-instrumentation
npx tsx --require ./dist/register.js examples/span-with-auto-llm.ts

# Or with Bun (use --preload instead of --require)
bun --preload ./dist/register.js examples/span-with-auto-llm.ts
```

**Important**: The `--require` flag is necessary for OpenAI auto-instrumentation to work. Without it, OpenAI calls won't be traced.

### 3. Span Usage Patterns (`span-usage.ts`)

Shows various ways to use the span API including sync/async patterns.

```bash
npx tsx examples/span-usage.ts
```

### 4. Span with Environment Variables (`span-with-env.ts`)

Demonstrates using environment-specific span attributes.

```bash
npx tsx examples/span-with-env.ts
```

### 5. Streaming (`streaming.ts`)

Shows how to handle streaming responses with proper span lifecycle management.

```bash
# With manual instrumentation
npx tsx examples/streaming.ts

# With auto-instrumentation
npx tsx --require ./dist/register.js examples/streaming.ts
```

## Important Notes

### Auto-instrumentation Requires --require Flag

The `autoLlm: true` configuration option has significant limitations and only works with strict import ordering. For reliable auto-instrumentation, you must use:

```bash
npx tsx --require ./dist/register.js your-script.ts
```

This ensures:

- ✅ OpenAI is instrumented before your code runs
- ✅ Parent-child span relationships work correctly
- ✅ No import order issues
- ✅ Works reliably in all scenarios

Note: While `autoLlm: true` can work with careful dynamic import ordering, it's not recommended due to reliability issues. See [AUTO_LLM_CONSTRAINTS.md](../AUTO_LLM_CONSTRAINTS.md) for technical details.

### Parent-Child Span Relationships

When using `--require ./dist/register.js`, manual spans created with `span()` will correctly appear as parents of auto-instrumented OpenAI calls:

```typescript
await span("parent-operation", async () => {
  // This OpenAI call will be a child of "parent-operation"
  const response = await openai.chat.completions.create({...});
});
```

## Troubleshooting

1. **OpenAI calls not being traced**: Make sure you're using `--require ./dist/register.js`
2. **Module not found errors**: Run `bun run build` to rebuild the SDK
3. **Invalid project ID**: Ensure `LILYPAD_PROJECT_ID` is a valid UUID
4. **Traces not appearing**: Wait 5-10 seconds for BatchSpanProcessor to export

## Viewing Traces

After running an example, you'll see output like:

```
[Lilypad] View trace: https://staging.lilypad.so/projects/xxx/traces/yyy
```

Click the link to view your trace in the Lilypad dashboard.
