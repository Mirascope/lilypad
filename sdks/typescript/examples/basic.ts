import lilypad from '../src';
import OpenAI from 'openai';

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    console.error('Please set OPENAI_API_KEY environment variable');
    process.exit(1);
  }

  // Configure Lilypad SDK
  await lilypad.configure({
    apiKey: process.env.LILYPAD_API_KEY || 'test-api-key',
    projectId: process.env.LILYPAD_PROJECT_ID || 'test-project-id',
    logLevel: 'info',
    auto_llm: true, // Enable automatic OpenAI instrumentation
  });

  // Create OpenAI client
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  console.log('Making OpenAI API call...\n');

  // Example 1: Simple completion
  const completion = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Say hello in 3 different languages' }],
    temperature: 0.7,
    max_tokens: 100,
  });

  console.log('Response:', completion.choices[0].message.content);
  console.log('\n---\n');

  // Example 2: System message with user prompt
  const systemCompletion = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'system', content: 'You are a helpful coding assistant.' },
      { role: 'user', content: 'Write a simple hello world function in Python' },
    ],
    temperature: 0.5,
    max_tokens: 150,
  });

  console.log('Code example:', systemCompletion.choices[0].message.content);

  // All OpenAI calls are automatically traced by Lilypad!
  // Check your Lilypad dashboard to see the traces

  // Shutdown SDK
  await lilypad.shutdown();
  console.log('\nSDK shutdown complete');
}

// Run the example
main().catch(console.error);
