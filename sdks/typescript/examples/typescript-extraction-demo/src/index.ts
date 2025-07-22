/**
 * TypeScript Extraction Demo with OpenAI Integration
 *
 * This example demonstrates:
 * 1. TypeScript code extraction at build time
 * 2. Automatic OpenAI instrumentation with auto_llm
 * 3. Versioned functions with TypeScript types preserved
 */

// Load environment variables
import * as dotenv from 'dotenv';
dotenv.config();

import lilypad from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

// IMPORTANT: Configure Lilypad BEFORE importing traced functions
// This ensures the SDK is ready when functions are defined
lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
  baseUrl: process.env.LILYPAD_BASE_URL || 'https://staging-api.lilypad.so/v0',
  autoLlm: true, // Enable automatic OpenAI instrumentation
});

// Import utilities that don't have traced functions
import { displayExtractedCode } from './utils/display';

// Import trace after configuration
import { trace } from '@lilypad/typescript-sdk';

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// New versioned function that uses OpenAI
const answerQuestion = trace(
  async (question: string): Promise<string> => {
    console.log(`Answering question: ${question}`);

    // This OpenAI call will be automatically traced with auto_llm
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'user',
          content: `Answer this question concisely: ${question}`,
        },
      ],
    });

    return completion.choices[0].message.content || 'No answer available';
  },
  {
    versioning: 'automatic',
    name: 'answerQuestion',
    tags: ['openai', 'qa'],
  },
);

// Function that analyzes order sentiment using OpenAI
const analyzeOrderSentiment = trace(
  async (
    orderFeedback: string,
  ): Promise<{
    sentiment: 'positive' | 'neutral' | 'negative';
    confidence: number;
    summary: string;
  }> => {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content:
            'Analyze the sentiment of customer feedback. Return JSON with sentiment (positive/neutral/negative), confidence (0-1), and a brief summary.',
        },
        {
          role: 'user',
          content: orderFeedback,
        },
      ],
      response_format: { type: 'json_object' },
    });

    const result = JSON.parse(response.choices[0].message.content || '{}');
    return {
      sentiment: result.sentiment || 'neutral',
      confidence: result.confidence || 0.5,
      summary: result.summary || 'No analysis available',
    };
  },
  { versioning: 'automatic', name: 'analyzeOrderSentiment' },
);

async function main() {
  console.log('🚀 TypeScript Extraction Demo with OpenAI Integration\n');

  // 1. Display extracted TypeScript code
  console.log('1️⃣  Checking extracted TypeScript code...\n');
  displayExtractedCode();

  // 2. Execute versioned functions
  console.log('\n2️⃣  Executing versioned functions...\n');

  // Dynamically import traced functions AFTER SDK is configured
  const { calculateDiscount, processOrder, validateUser, generateReport } = await import(
    './services/business-logic'
  );

  // Test business logic functions
  const discount = await calculateDiscount({
    originalPrice: 100,
    customerTier: 'gold',
    quantity: 5,
  });
  console.log('✅ Discount calculated:', discount);

  const order = await processOrder({
    items: [
      { id: '1', name: 'Laptop', price: 999.99, quantity: 1 },
      { id: '2', name: 'Mouse', price: 29.99, quantity: 2 },
    ],
    customerId: 'cust-123',
    shippingMethod: 'express',
  });
  console.log('✅ Order processed:', order.orderId);

  // 3. Test OpenAI functions (if API key is available)
  console.log('\n3️⃣  Testing OpenAI integration...\n');

  if (process.env.OPENAI_API_KEY) {
    try {
      // Test question answering
      const answer = await answerQuestion('What is TypeScript?');
      console.log('Q: What is TypeScript?');
      console.log('A:', answer);

      // Test sentiment analysis
      const sentiment = await analyzeOrderSentiment(
        'The laptop arrived quickly and works perfectly! Great service!',
      );
      console.log('\nSentiment analysis:', sentiment);
    } catch (error) {
      console.log('⚠️  OpenAI tests skipped (API error):', (error as Error).message);
    }
  } else {
    console.log('⚠️  OpenAI tests skipped (no API key)');
    console.log('   Set OPENAI_API_KEY to test OpenAI integration');
  }

  // 4. TypeScript extraction is done at build time
  console.log('\n4️⃣  TypeScript extraction status...\n');

  const functions = [
    { name: 'calculateDiscount', fn: calculateDiscount },
    { name: 'answerQuestion', fn: answerQuestion },
    { name: 'analyzeOrderSentiment', fn: analyzeOrderSentiment },
  ];

  // Check if metadata was extracted for these functions
  try {
    const metadata = await import('../lilypad-metadata.json');
    for (const { name } of functions) {
      const extracted = Object.values(metadata.functions).some((f: any) => f.name === name);
      console.log(`${name}: ${extracted ? '✅ TypeScript extracted' : '❌ Not extracted'}`);
    }
  } catch (error) {
    console.log('❌ Metadata file not found - run npm run extract first');
  }

  console.log('\n✅ Demo complete!');
  console.log('\n📝 Key features demonstrated:');
  console.log('   • TypeScript code extraction at build time');
  console.log('   • Automatic versioning with type preservation');
  console.log('   • OpenAI instrumentation with auto_llm');
  console.log('   • Multiple function types (sync, async, generic)');
}

// Run the demo
main()
  .catch(console.error)
  .finally(() => lilypad.shutdown());
