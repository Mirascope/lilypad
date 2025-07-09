/**
 * Basic autoLlm example with TypeScript
 *
 * Run with:
 *   export $(cat .env | xargs) && tsx --require ../dist/register-improved.js basic-auto-llm.ts
 */

import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function main() {
  console.log('🚀 Basic autoLlm example\n');

  const completion = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'What is the capital of France?' },
    ],
  });

  console.log('Response:', completion.choices[0].message.content);
  console.log('\n✅ Trace URL:');
  console.log(
    `${process.env.LILYPAD_REMOTE_CLIENT_URL}/projects/${process.env.LILYPAD_PROJECT_ID}/traces`,
  );
}

main()
  .then(() => {
    // Wait for BatchSpanProcessor to export (default export interval is 5 seconds)
    console.log('\nWaiting for traces to export...');
    setTimeout(() => {
      console.log('Done!');
      process.exit(0);
    }, 6000); // Wait 6 seconds to ensure export happens
  })
  .catch(console.error);
