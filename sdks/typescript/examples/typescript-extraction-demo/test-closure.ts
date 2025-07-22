/**
 * Test to verify TypeScript code extraction works correctly
 */

// @ts-ignore
import lilypad, { trace } from '@lilypad/typescript-sdk';
// Direct import from source to test
// @ts-ignore
import { getCachedClosure } from '../../src/utils/closure';

// Configure SDK
lilypad.configure({
  apiKey: 'test',
  projectId: 'test',
  logLevel: 'debug',
});

// Test function with TypeScript types
const testFunction = trace(
  async (name: string, age: number): Promise<{ greeting: string; isAdult: boolean }> => {
    const greeting = `Hello ${name}, you are ${age} years old`;
    return {
      greeting,
      isAdult: age >= 18,
    };
  },
  { versioning: 'automatic', name: 'testFunction' },
);

// Test closure extraction
console.log('\n🔍 Testing TypeScript code extraction...\n');

// Get closure for versioned function
const closure = getCachedClosure(testFunction as any, undefined, true, 'testFunction');

console.log('📦 Closure extracted:');
console.log('  Name:', closure.name);
console.log('  Hash:', closure.hash);
console.log('  Code length:', closure.code.length);
console.log('  Is TypeScript:', closure.code.includes(': ') || closure.code.includes('Promise<'));
console.log('\n📝 Code:');
console.log('─'.repeat(80));
console.log(closure.code);
console.log('─'.repeat(80));

// Check if it's TypeScript or JavaScript
if (closure.code.includes('Promise<') && closure.code.includes(': ')) {
  console.log('\n✅ SUCCESS: TypeScript code is being used!');
} else {
  console.log('\n❌ FAILURE: JavaScript code is being used instead of TypeScript');
}
