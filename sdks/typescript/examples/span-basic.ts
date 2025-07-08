/**
 * Basic example demonstrating the span functionality in Lilypad TypeScript SDK
 * This matches the Python SDK's span API
 */

import lilypad from '../src';

// Configure the SDK (replace with your actual credentials)
lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY || 'your-api-key',
  projectId: process.env.LILYPAD_PROJECT_ID || 'your-project-id',
  baseUrl: process.env.LILYPAD_BASE_URL || 'http://localhost:8000/v0',
  logLevel: 'debug',
});

async function main() {
  // Example 1: Using span() for async operations (most common)
  const result = await lilypad.span('fetch-user-data', async (span) => {
    span.info('Starting to fetch user data');
    span.metadata({ userId: 123, source: 'database' });

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 100));

    const userData = { id: 123, name: 'Alice', role: 'admin' };
    span.info('User data fetched successfully');

    return userData;
  });

  console.log('User data:', result);

  // Example 2: Using syncSpan() for synchronous operations
  const total = lilypad.syncSpan('calculate-total', (span) => {
    const items = [10, 20, 30, 40, 50];
    span.metadata({ itemCount: items.length });

    const sum = items.reduce((a, b) => a + b, 0);
    span.info(`Calculated total: ${sum}`);

    return sum;
  });

  console.log('Total:', total);

  // Example 3: Manual span management (for more control)
  const manualSpan = new lilypad.Span('manual-operation');
  try {
    manualSpan.metadata({ operation: 'data-processing' });
    manualSpan.debug('Starting manual operation');

    // Do some work...
    await new Promise((resolve) => setTimeout(resolve, 50));

    manualSpan.info('Operation completed');
  } catch (error) {
    manualSpan.recordException(error);
    throw error;
  } finally {
    manualSpan.finish();
  }

  // Example 4: Using spans with sessions
  await lilypad.sessionAsync('user-session-123', async (session) => {
    console.log('Session ID:', session.id);

    // Spans created within this session will automatically have the session ID
    await lilypad.span('session-operation', async (span) => {
      span.info('This span is associated with the session');
      // The span automatically has lilypad.session_id = 'user-session-123'
    });
  });

  // Example 5: Error handling with spans
  try {
    await lilypad.span('risky-operation', async (span) => {
      span.warning('Attempting risky operation');

      // Simulate an error
      throw new Error('Something went wrong!');
    });
  } catch (error) {
    console.error('Operation failed:', error);
    // The span automatically recorded the exception and set ERROR status
  }

  // Shutdown to ensure all spans are exported
  await lilypad.shutdown();
}

// Run the example
main().catch(console.error);
