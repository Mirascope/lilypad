import lilypad from '../dist';

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    console.error('Please set OPENAI_API_KEY environment variable');
    process.exit(1);
  }

  // Configure Lilypad SDK
  await lilypad.configure({
    apiKey: process.env.LILYPAD_API_KEY,
    projectId: process.env.LILYPAD_PROJECT_ID,
    logLevel: 'debug', // Changed to debug for more detailed logs
  });

  // Import and create OpenAI client
  const OpenAI = (await import('openai')).default;
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  console.log('Making OpenAI API call with manual tracing...\n');

  // Example 1: Simple completion (manually traced)
  const completion = await lilypad.traceOpenAICompletion(
    {
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: 'Say hello in 3 different languages' }],
      temperature: 0.7,
    },
    () =>
      openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: 'Say hello in 3 different languages' }],
        temperature: 0.7,
      }),
  );

  console.log('Response:', completion.choices[0].message.content);
  console.log('\n---\n');

  // Example 2: System message with user prompt (manually traced)
  const systemCompletion = await lilypad.traceOpenAICompletion(
    {
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a helpful coding assistant.' },
        { role: 'user', content: 'Write a simple hello world function in Python' },
      ],
      temperature: 0.5,
      max_tokens: 150,
    },
    () =>
      openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: 'You are a helpful coding assistant.' },
          { role: 'user', content: 'Write a simple hello world function in Python' },
        ],
        temperature: 0.5,
        max_tokens: 150,
      }),
  );

  console.log('Code example:', systemCompletion.choices[0].message.content);

  // Note: This example uses manual tracing. For automatic tracing, run with:
  // npx tsx --require ../dist/register.cjs examples/basic-auto.ts

  // Shutdown SDK
  await lilypad.shutdown();
  console.log('\nSDK shutdown complete');
}

// Run the example
main().catch(console.error);
