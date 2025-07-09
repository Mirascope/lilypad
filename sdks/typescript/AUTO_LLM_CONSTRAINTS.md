# AutoLLM Import Order Constraint

## Important Limitation

When using the `autoLlm: true` option, there is a critical constraint regarding module import order:

### ❌ This will NOT work:
```typescript
import OpenAI from "openai";  // OpenAI imported BEFORE configure()
import { configure } from "lilypad";

await configure({ 
  autoLlm: true  // Hook cannot intercept already-loaded module
});

const client = new OpenAI();  // Will NOT be instrumented
```

### ✅ This WILL work:
```typescript
import { configure } from "lilypad";

// Configure FIRST
await configure({ 
  autoLlm: true 
});

// Import OpenAI AFTER configure()
const { default: OpenAI } = await import("openai");
const client = new OpenAI();  // Will be instrumented correctly
```

## Technical Explanation

The `autoLlm` feature uses Node.js `Module._load` hooks to intercept and wrap the OpenAI module at load time. This approach has an inherent limitation:

- **Module._load hooks only work when a module is loaded for the first time**
- If the module is already in the require cache, the hook will not be triggered
- This is a fundamental constraint of Node.js module system, not specific to our implementation

## Recommended Approaches

### 1. Use Dynamic Import (Most Flexible)
```typescript
await configure({ autoLlm: true });
const { default: OpenAI } = await import("openai");
```

### 2. Use --require Flag (Most Reliable)
```bash
node --require ./dist/register.js your-app.js
```
This ensures hooks are installed before any application code runs.

### 3. Manual Wrapping (Most Control)
```typescript
import OpenAI from "openai";
import { wrapOpenAI } from "lilypad";

const client = wrapOpenAI(new OpenAI());
```

## Framework-Specific Considerations

- **Next.js**: Use dynamic imports in API routes or server components
- **Express**: Configure Lilypad in the main entry point before importing route handlers
- **NestJS**: Configure in the bootstrap function before module initialization
- **Serverless**: Use the --require approach or manual wrapping

## Debugging Tips

If OpenAI calls are not being traced:

1. Enable debug logging: `logger.setLevel('debug')`
2. Check console for "OpenAI module loaded via Module._load" message
3. Verify import order - OpenAI must be imported AFTER configure()
4. Consider using `--require` flag for guaranteed instrumentation