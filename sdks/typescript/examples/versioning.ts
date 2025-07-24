/**
 * Simple versioning example
 * Run with: bun run examples/versioning-simple.ts
 */

import OpenAI from 'openai';
import lilypad, { trace, wrapWithTrace } from '@lilypad/typescript-sdk';

// Configure Lilypad
lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY || 'test-api-key',
  baseUrl: process.env.LILYPAD_BASE_URL || 'http://localhost:8000',
  projectId: process.env.LILYPAD_PROJECT_ID || 'test-project',
});

// Service with versioned methods
class MyService {
  constructor(private client: OpenAI) {}

  @trace({ versioning: 'automatic' })
  async generateText(prompt: string): Promise<string | null> {
    const response = await this.client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
    });
    return response.choices[0].message.content;
  }
}

async function main() {
  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const service = new MyService(client);

  const result = await service.generateText('Where is the capital of France?');
  console.log('Result:', result);

  // Check versions
  const versions = await service.generateText.versions();
  console.log('Versions:', versions.length);

  // Execute specific version
  if (versions.length > 0) {
    const v1 = service.generateText.version(1);
    const v1Result = await v1.call(service, 'world');
    console.log('V1 result:', v1Result);
  }

  await lilypad.shutdown();
}

main().catch(console.error);
