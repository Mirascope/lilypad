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
    autoLlm: true, // Enable automatic OpenAI instrumentation
  });

  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  console.log('Starting streaming example...\n');

  // Example: Streaming chat completion
  const stream = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'system',
        content: 'You are a creative storyteller.',
      },
      {
        role: 'user',
        content: 'Tell me a very short story about a robot learning to paint.',
      },
    ],
    stream: true,
    temperature: 0.8,
    max_tokens: 200,
  });

  console.log('Story:');
  console.log('------');

  // Process the stream
  let fullContent = '';
  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    fullContent += content;
    process.stdout.write(content);
  }

  console.log('\n------');
  console.log(`\nTotal characters: ${fullContent.length}`);

  // The streaming response is automatically traced by Lilypad
  // Check your Lilypad dashboard to see the trace!

  // Shutdown SDK
  await lilypad.shutdown();
  console.log('\nSDK shutdown complete');
}

// Run the example
main().catch(console.error);
