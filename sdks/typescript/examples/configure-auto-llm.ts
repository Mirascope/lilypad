/**
 * Using configure() with auto_llm in TypeScript
 *
 * Run with:
 *   export $(cat .env | xargs) && tsx configure-auto-llm.ts
 */

import { configure } from '../src';
import OpenAI from 'openai';

async function main() {
  console.log('⚙️  Configure auto_llm example\n');

  // Configure Lilypad with auto_llm
  await configure({
    apiKey: process.env.LILYPAD_API_KEY!,
    projectId: process.env.LILYPAD_PROJECT_ID!,
    baseUrl: process.env.LILYPAD_BASE_URL,
    auto_llm: true,
  });

  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  // Multiple calls to show batching
  const [response1, response2] = await Promise.all([
    openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: 'Say hello in English' }],
    }),
    openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: 'Say hello in Japanese' }],
    }),
  ]);

  console.log('Response 1:', response1.choices[0].message.content);
  console.log('Response 2:', response2.choices[0].message.content);

  console.log('\n✅ Trace URL:');
  console.log(
    `${process.env.LILYPAD_REMOTE_CLIENT_URL}/projects/${process.env.LILYPAD_PROJECT_ID}/traces`,
  );
}

main()
  .then(() => setTimeout(() => process.exit(0), 5000))
  .catch(console.error);
