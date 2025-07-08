/**
 * Test span functionality using .env file configuration
 */

import lilypad from '../src';

// Bun automatically loads .env file
console.log('Environment variables loaded:');
console.log('- LILYPAD_PROJECT_ID:', process.env.LILYPAD_PROJECT_ID);
console.log('- LILYPAD_API_KEY:', process.env.LILYPAD_API_KEY ? '***' + process.env.LILYPAD_API_KEY.slice(-4) : 'not set');
console.log('- LILYPAD_BASE_URL:', process.env.LILYPAD_BASE_URL);
console.log('');

// Configure using environment variables
lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
  baseUrl: process.env.LILYPAD_BASE_URL,
  remoteClientUrl: process.env.LILYPAD_REMOTE_CLIENT_URL,
  logLevel: 'debug',
});

async function main() {
  console.log('Testing Lilypad Span with .env configuration...\n');

  // Create a test span
  const result = await lilypad.span('env-test-operation', async (span) => {
    span.info('Testing with environment variables');
    span.metadata({
      environment: 'staging',
      source: '.env',
      timestamp: new Date().toISOString(),
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    span.info('Operation completed successfully');
    return { success: true };
  });
  
  console.log('Result:', result);
  
  // Wait a bit for the span to be exported
  console.log('\nWaiting for span export...');
  await new Promise(resolve => setTimeout(resolve, 6000));
  
  console.log('\nShutting down...');
  await lilypad.shutdown();
  
  console.log('\nTest completed!');
}

main().catch(console.error);