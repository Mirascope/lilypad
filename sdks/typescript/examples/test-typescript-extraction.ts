/**
 * Test TypeScript Code Extraction
 *
 * This example tests that TypeScript source code is captured at build time
 * and used instead of JavaScript code for versioned functions.
 *
 * Run:
 * 1. npm run build (to extract metadata)
 * 2. bun run examples/test-typescript-extraction.ts
 */

import lilypad, { trace } from '../src/index';
import { metadataLoader } from '../src/versioning/metadata-loader';

// Configure SDK
lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY || 'test-api-key',
  projectId: process.env.LILYPAD_PROJECT_ID || 'test-project-id',
  baseUrl: process.env.LILYPAD_BASE_URL || 'http://localhost:8000/v0',
});

// Define some functions with TypeScript-specific features
interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

// Function with TypeScript types and interfaces
const getUserInfo = trace(
  async (userId: number): Promise<User> => {
    console.log(`Fetching user info for ID: ${userId}`);

    // Simulate API call
    const user: User = {
      id: userId,
      name: `User ${userId}`,
      email: `user${userId}@example.com`,
      role: userId === 1 ? 'admin' : 'user',
    };

    return user;
  },
  { versioning: 'automatic', name: 'getUserInfo' },
);

// Function with generics
const processArray = trace(
  <T extends { id: number }>(items: T[]): T[] => {
    console.log(`Processing ${items.length} items`);
    return items.sort((a, b) => a.id - b.id);
  },
  { versioning: 'automatic', name: 'processArray' },
);

// Function with destructuring and default parameters
const calculatePrice = trace(
  ({
    basePrice,
    tax = 0.08,
    discount = 0,
  }: {
    basePrice: number;
    tax?: number;
    discount?: number;
  }): number => {
    const discountedPrice = basePrice * (1 - discount);
    const finalPrice = discountedPrice * (1 + tax);
    return Math.round(finalPrice * 100) / 100;
  },
  { versioning: 'automatic', name: 'calculatePrice' },
);

// Arrow function with type annotations
const formatUserGreeting = trace(
  (user: User, time: 'morning' | 'afternoon' | 'evening' = 'morning'): string => {
    const greetings = {
      morning: 'Good morning',
      afternoon: 'Good afternoon',
      evening: 'Good evening',
    };

    return `${greetings[time]}, ${user.name}!`;
  },
  { versioning: 'automatic', name: 'formatUserGreeting' },
);

async function runTests() {
  console.log('=== Testing TypeScript Code Extraction ===\n');

  // Check if metadata is loaded
  console.log('1. Checking metadata availability:');
  const hasMetadata = metadataLoader.hasMetadata();
  console.log(`   Metadata available: ${hasMetadata ? '✅ Yes' : '❌ No'}`);

  if (hasMetadata) {
    console.log('\n2. Available functions in metadata:');
    const allFunctions = metadataLoader.getAllFunctions();
    allFunctions.forEach((fn) => {
      console.log(`   - ${fn.name} (${fn.filePath}:${fn.startLine}-${fn.endLine})`);
    });
  }

  console.log('\n3. Testing function execution:');

  // Test getUserInfo
  const user = await getUserInfo(1);
  console.log(`   getUserInfo result:`, user);

  // Test processArray
  const items = [
    { id: 3, name: 'Item 3' },
    { id: 1, name: 'Item 1' },
    { id: 2, name: 'Item 2' },
  ];
  const sorted = processArray(items);
  console.log(`   processArray result:`, sorted);

  // Test calculatePrice
  const price = calculatePrice({ basePrice: 100, discount: 0.1 });
  console.log(`   calculatePrice result: $${price}`);

  // Test formatUserGreeting
  const greeting = formatUserGreeting(user, 'afternoon');
  console.log(`   formatUserGreeting result: ${greeting}`);

  console.log('\n4. Checking captured code:');

  // For each function, check if we have TypeScript or JavaScript code
  const functions = [getUserInfo, processArray, calculatePrice, formatUserGreeting];
  const functionNames = ['getUserInfo', 'processArray', 'calculatePrice', 'formatUserGreeting'];

  for (let i = 0; i < functions.length; i++) {
    const fn = functions[i];
    const name = functionNames[i];

    // Check if the function has versions method (indicates versioning is enabled)
    if (typeof (fn as any).versions === 'function') {
      console.log(`\n   ${name}:`);

      // The actual code would be sent to the server during execution
      // Here we just check if metadata contains TypeScript code
      const metadata = metadataLoader.getByName(name);
      if (metadata) {
        console.log('   ✅ TypeScript source available in metadata');
        console.log('   Code preview:');
        const lines = metadata.sourceCode.split('\n').slice(0, 3);
        lines.forEach((line) => console.log(`      ${line}`));
        console.log('      ...');
      } else {
        console.log('   ❌ No TypeScript metadata found');
      }
    }
  }

  console.log('\n5. Build Instructions:');
  console.log('   To enable TypeScript code extraction:');
  console.log('   1. Run: npm run build');
  console.log('   2. This extracts TypeScript source during build');
  console.log('   3. The metadata is saved to dist/versioning-metadata.json');
  console.log('   4. At runtime, versioned functions will use TypeScript code');

  console.log('\n✅ Test complete!');
}

// Run the tests
runTests()
  .catch(console.error)
  .finally(() => lilypad.shutdown());
