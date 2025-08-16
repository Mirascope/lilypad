# Lilypad TypeScript SDK

The official TypeScript library for the Lilypad API, providing OpenTelemetry instrumentation for LLM observability.

## Installation

```bash
npm install @mirascope/lilypad-sdk
```

## Usage

```typescript
import lilypad from '@mirascope/lilypad-sdk';
import OpenAI from 'openai';

lilypad.configure({ mode: 'debug' });

const client = new OpenAI();
lilypad.instrument_openai(client);

const completion = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

When configured in debug mode, telemetry data will be output to the console.

Note: This SDK is currently in alpha and falls under the top-level enterprise license.
