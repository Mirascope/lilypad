# Auto-LLM Instrumentation Constraints in TypeScript

## ⚠️ Important: autoLlm Option Does Not Work

**The `autoLlm: true` configuration option does not work reliably in practice.** While the documentation below explains the theoretical constraints, in reality, even with correct import order, the instrumentation fails due to various technical issues.

## Recommended Solution: Use --require Flag

```bash
# ✅ THIS WORKS - Use this approach
npx tsx --require ./dist/register.js your-script.ts

# ❌ THIS DOESN'T WORK - Don't use autoLlm
await configure({ autoLlm: true });
```

## Why autoLlm Fails

### 1. Module Loading Order Issues
Even with dynamic imports after `configure()`, the instrumentation is unreliable:

```typescript
// ❌ Theoretically correct but doesn't work in practice
await configure({ autoLlm: true });
const { default: OpenAI } = await import('openai');
```

### 2. ImportInTheMiddle Errors
The OpenTelemetry instrumentation library throws errors:
```
TypeError: ImportInTheMiddle is not a constructor
```

### 3. Context Manager Conflicts
Multiple TracerProvider instances can be created, breaking parent-child span relationships.

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

### Why Module._load Hooks Don't Work Well

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

## Conclusion

The `autoLlm` option is effectively deprecated. Always use `--require ./dist/register.js` for reliable OpenAI auto-instrumentation.