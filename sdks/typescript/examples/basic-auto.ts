import OpenAI from 'openai';

// With autoLlm: true, you don't need to call lilypad.configure() in this file
// register.ts will automatically instrument OpenAI

async function main() {
  console.log('Starting OpenAI example with auto instrumentation...');

  // Create OpenAI client
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  try {
    // Simple chat completion request
    console.log('\n1. Simple chat completion:');
    const completion = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful assistant.',
        },
        {
          role: 'user',
          content: 'Say hello in Japanese!',
        },
      ],
      temperature: 0.7,
      max_tokens: 50,
    });

    console.log('Response:', completion.choices[0]?.message?.content);

    // Streaming response example
    console.log('\n2. Streaming chat completion:');
    const stream = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'user',
          content: 'Count from 1 to 5 slowly',
        },
      ],
      stream: true,
    });

    process.stdout.write('Streaming response: ');
    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        process.stdout.write(content);
      }
    }
    console.log('\n');

    console.log('✅ All OpenAI calls were automatically traced!');
    console.log('Check your Lilypad dashboard to see the traces.');
  } catch (error) {
    console.error('Error:', error);
  }
}

// Run the main function
main().catch(console.error);
