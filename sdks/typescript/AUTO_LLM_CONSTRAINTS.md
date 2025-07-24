# Auto-LLM Instrumentation Constraints in TypeScript

## ⚠️ Important: autoLlm Option Has Limited Reliability

**The `autoLlm: true` configuration option has significant limitations and only works under specific conditions.** While it can work in some cases, the `--require` flag is much more reliable.

## Recommended Solution: Use --require Flag

```bash
# ✅ THIS WORKS - Use this approach
npx tsx --require ./dist/register.js your-script.ts

# ❌ THIS DOESN'T WORK - Don't use autoLlm
await configure({ autoLlm: true });
```

## When autoLlm Might Work

The `autoLlm` option can work in simple cases if you strictly follow the import order:

```typescript
// ✅ This might work (but not guaranteed)
await configure({ autoLlm: true });
const { default: OpenAI } = await import('openai'); // Dynamic import AFTER configure
```

However, it often fails due to:

### 1. ImportInTheMiddle Errors

The OpenTelemetry instrumentation library throws errors:

```
TypeError: ImportInTheMiddle is not a constructor
```

### 2. Context Manager Conflicts

Multiple TracerProvider instances can be created, breaking parent-child span relationships.

### 3. Module Cache Issues

If OpenAI is already in the module cache (from another file), instrumentation won't apply.

## The Working Solution: register.js

Using `--require ./dist/register.js` ensures:

1. **Instrumentation loads first**: Before any application code
2. **Consistent behavior**: Always works, regardless of your code structure
3. **Parent-child relationships**: Manual spans correctly nest auto-instrumented calls
4. **No code changes needed**: Existing OpenAI code is automatically traced

### How to Use

```bash
# Set required environment variables
export LILYPAD_API_KEY="your-api-key"
export LILYPAD_PROJECT_ID="your-project-id"
export OPENAI_API_KEY="your-openai-key"

# Run with --require flag
npx tsx --require ./dist/register.js your-script.ts

# Or with Bun (use --preload)
bun --preload ./dist/register.js your-script.ts
```

### Example Code

```typescript
// your-script.ts
import OpenAI from 'openai';
import { configure, span } from 'lilypad';

// Configure SDK (DON'T use autoLlm: true)
await configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
});

const openai = new OpenAI();

// Manual span will be parent of auto-instrumented OpenAI call
await span('process-request', async (s) => {
  s.metadata({ userId: '123' });

  // This call is automatically traced as a child span
  const response = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: 'Hello!' }],
  });

  s.metadata({ responseId: response.id });
});
```

## Technical Background

### Why Module.\_load Hooks Don't Work Well

Node.js module loading is complex, especially with:

- TypeScript transpilation
- ESM vs CommonJS interop
- Module caching
- Async module loading

The `Module._load` approach that `autoLlm` uses has too many edge cases and failure modes.

### ESM Module Loading Phases

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌────────────┐
│ Resolution  │ --> │   Parsing   │ --> │Instantiation │ --> │ Evaluation │
└─────────────┘     └─────────────┘     └──────────────┘     └────────────┘
```

Instrumentation must happen before Evaluation, which is why `--require` works (it runs first) while `autoLlm` fails (it runs too late).

## Migration Guide

If you're currently trying to use `autoLlm: true`:

1. Remove `autoLlm: true` from your `configure()` call
2. Keep your existing imports as-is (no need for dynamic imports)
3. Run your script with `--require ./dist/register.js`

```diff
// Before (not working)
await configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
- autoLlm: true,
});

// After (working)
await configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
});
```

Then run with:

```bash
npx tsx --require ./dist/register.js your-script.ts
```

## Summary: When to Use Each Approach

### Use `--require` (Recommended)

- ✅ Always works reliably
- ✅ No import order constraints
- ✅ Works with existing code
- ✅ Proper parent-child span relationships

### Use `autoLlm: true` (Limited Use Cases)

- ⚠️ Only works with strict dynamic import order
- ⚠️ May fail with ImportInTheMiddle errors
- ⚠️ Not recommended for production
- ✅ Might be useful if you can't modify the startup command

## Conclusion

While `autoLlm` can work in specific scenarios with careful import ordering, the `--require ./dist/register.js` approach is strongly recommended for its reliability and ease of use.
