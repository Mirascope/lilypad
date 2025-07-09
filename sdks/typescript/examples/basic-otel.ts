/**
 * Example using OTel-compliant auto-instrumentation
 *
 * Run with:
 *   node --require ../dist/register-otel.js basic-otel.js
 * Or:
 *   tsx --require ../dist/register-otel.js basic-otel.ts
 */

import OpenAI from 'openai';

// Create OpenAI client - no Lilypad-specific code needed!
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function main() {
  try {
    console.log('Making OpenAI request with OTel auto-instrumentation...');

    // This call will be automatically traced
    const completion = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: 'You are a helpful assistant.' },
        { role: 'user', content: 'What is the capital of France?' },
      ],
    });

    console.log('Response:', completion.choices[0].message.content);
    console.log('Trace should be sent to Lilypad automatically!');
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
