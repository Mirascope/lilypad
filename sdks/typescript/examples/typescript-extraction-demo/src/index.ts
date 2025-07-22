/**
 * TypeScript Extraction Demo with OpenAI Integration
 *
 * This example demonstrates:
 * 1. TypeScript code extraction at build time
 * 2. Dependency extraction (functions, types, constants)
 * 3. Automatic OpenAI instrumentation with auto_llm
 * 4. Versioned functions with TypeScript types preserved
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

// Dependencies that will be captured automatically
interface Product {
  id: string;
  name: string;
  price: number;
}

interface User {
  name: string;
  age: number;
  premium: boolean;
}

const TAX_RATE = 0.08;
const PREMIUM_DISCOUNT = 0.15;
const SENIOR_DISCOUNT = 0.1;

// Helper functions that will be captured as dependencies
function formatUser(user: User): string {
  return `${user.name} (${user.age} years old)`;
}

function calculateDiscountRate(user: User): number {
  if (user.age >= 65) return SENIOR_DISCOUNT;
  if (user.premium) return PREMIUM_DISCOUNT;
  return 0;
}

function formatCurrency(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

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

// Function with multiple dependencies (demonstrates dependency extraction)
const calculateTotal = trace(
  function (products: Product[], user: User) {
    console.log(`Processing order for: ${formatUser(user)}`);

    let subtotal = 0;
    for (const product of products) {
      const discount = calculateDiscountRate(user);
      const discountedPrice = product.price * (1 - discount);
      subtotal += discountedPrice;
      console.log(
        `- ${product.name}: ${formatCurrency(discountedPrice)} (${(discount * 100).toFixed(0)}% off)`,
      );
    }

    const tax = subtotal * TAX_RATE;
    const total = subtotal + tax;

    console.log(`Subtotal: ${formatCurrency(subtotal)}`);
    console.log(`Tax: ${formatCurrency(tax)}`);
    console.log(`Total: ${formatCurrency(total)}`);

    return total;
  },
  {
    versioning: 'automatic',
    name: 'calculateTotal',
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

  // 3. Test dependency extraction function
  console.log('\n3️⃣  Testing dependency extraction...\n');

  const products: Product[] = [
    { id: '1', name: 'TypeScript Book', price: 45.99 },
    { id: '2', name: 'Code Editor License', price: 79.99 },
    { id: '3', name: 'Coffee Mug', price: 12.99 },
  ];

  const youngUser: User = { name: 'Alice', age: 16, premium: false };
  const premiumUser: User = { name: 'Bob', age: 35, premium: true };
  const seniorUser: User = { name: 'Carol', age: 68, premium: false };

  console.log('=== Young User ===');
  await calculateTotal(products, youngUser);

  console.log('\n=== Premium User ===');
  await calculateTotal(products, premiumUser);

  console.log('\n=== Senior User ===');
  await calculateTotal(products, seniorUser);

  // 4. Test OpenAI functions (if API key is available)
  console.log('\n4️⃣  Testing OpenAI integration...\n');

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

  // 5. TypeScript extraction is done at build time
  console.log('\n5️⃣  TypeScript extraction status...\n');

  const functions = [
    { name: 'calculateDiscount', fn: calculateDiscount },
    { name: 'calculateTotal', fn: calculateTotal },
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
  console.log('   • Dependency extraction (functions, types, constants)');
  console.log('   • Self-contained code blocks with all dependencies');
  console.log('   • Automatic versioning with type preservation');
  console.log('   • OpenAI instrumentation with auto_llm');
  console.log('   • Multiple function types (sync, async, generic)');
  console.log('\n💡 The calculateTotal function demonstrates dependency extraction:');
  console.log('   • Captures formatUser and calculateDiscountRate functions');
  console.log('   • Captures Product and User interfaces');
  console.log('   • Captures TAX_RATE, PREMIUM_DISCOUNT, SENIOR_DISCOUNT constants');
  console.log('   • All dependencies are included in the self-contained code!');
}

// Run the demo
main()
  .catch(console.error)
  .finally(() => lilypad.shutdown());
