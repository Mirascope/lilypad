import { span, configure } from '../src';
import OpenAI from 'openai';

// Note: When running with --require flag, you may see ImportInTheMiddle errors.
// These are harmless warnings and don't affect functionality.

// IMPORTANT: This example demonstrates using both manual spans and auto-LLM instrumentation.
// When using --require ./dist/register.js:
//   - OpenAI calls are automatically instrumented by register.js
//   - We still need to call configure() to enable manual span() function
//   - Don't set autoLlm:true here as register.js already handles it

async function main() {
  // Configure SDK to enable manual span() function
  await configure({
    apiKey: process.env.LILYPAD_API_KEY!,
    projectId: process.env.LILYPAD_PROJECT_ID!,
    logLevel: 'debug', // Enable debug logging
    // Don't set autoLlm here - it's already handled by register.js
  });

  // Initialize OpenAI client - it will be automatically instrumented by register.js
  const client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY!,
  });

  async function answerQuestion(question: string): Promise<string | null> {
    const response = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: `Answer this question: ${question}` }],
    });

    return response.choices[0].message.content;
  }

  // Create a local span that wraps the LLM call
  await span('local_span', async (s) => {
    // Log the span context
    console.log(`[DEBUG] Parent span ID: ${s.span_id}`);
    console.log(`[DEBUG] Parent span context:`, s.context);

    const response = await answerQuestion('What is the capital of France?');
    console.log(response);
  });
}

// Run the example
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
