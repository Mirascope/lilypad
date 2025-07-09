/**
 * Streaming example with auto_llm
 *
 * Run with:
 *   export $(cat .env | xargs) && tsx --require ../dist/register-improved.js streaming-auto-llm.ts
 */

import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function main() {
  console.log('🌊 Streaming auto_llm example\n');

  const stream = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: 'Write a haiku about TypeScript' }],
    stream: true,
  });

  console.log('Streaming response:');
  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) {
      process.stdout.write(content);
    }
  }

  console.log('\n\n✅ Trace URL:');
  console.log(
    `${process.env.LILYPAD_REMOTE_CLIENT_URL}/projects/${process.env.LILYPAD_PROJECT_ID}/traces`,
  );
}

main().catch(console.error);
