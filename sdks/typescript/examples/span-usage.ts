/**
 * Example demonstrating the new span functionality in Lilypad TypeScript SDK
 */

import lilypad from '../src';

// Configure the SDK
lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY || 'your-api-key',
  projectId: process.env.LILYPAD_PROJECT_ID || 'your-project-id',
  baseUrl: process.env.LILYPAD_BASE_URL,
  logLevel: 'debug',
});

// Example 1: Manual span management
async function manualSpanExample() {
  console.log('\n=== Manual Span Example ===');

  const span = new lilypad.Span('manual-operation');

  try {
    span.metadata({ userId: 123, operation: 'data-processing' });
    span.info('Starting data processing');

    // Simulate some work
    await new Promise((resolve) => setTimeout(resolve, 100));

    span.info('Processing completed successfully');
  } catch (error) {
    span.recordException(error);
    throw error;
  } finally {
    span.finish();
  }
}

// Example 2: Using span() helper for async operations
async function asyncSpanExample() {
  console.log('\n=== Async Span Example ===');

  const result = await lilypad.span('fetch-user-data', async (span) => {
    span.metadata({ endpoint: '/api/users/123' });
    span.info('Fetching user data from API');

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 200));

    const userData = { id: 123, name: 'John Doe', email: 'john@example.com' };

    span.info('User data fetched successfully');
    span.metadata({ responseSize: JSON.stringify(userData).length });

    return userData;
  });

  console.log('Fetched user:', result);
}

// Example 3: Using syncSpan() for synchronous operations
function syncSpanExample() {
  console.log('\n=== Sync Span Example ===');

  const result = lilypad.syncSpan('calculate-total', (span) => {
    const items = [
      { name: 'Product A', price: 10.99 },
      { name: 'Product B', price: 24.99 },
      { name: 'Product C', price: 5.99 },
    ];

    span.metadata({ itemCount: items.length });
    span.debug('Calculating total for items', { items });

    const total = items.reduce((sum, item) => sum + item.price, 0);

    span.info(`Total calculated: $${total.toFixed(2)}`);

    return total;
  });

  console.log('Total price:', result);
}

// Example 4: Nested spans
async function nestedSpansExample() {
  console.log('\n=== Nested Spans Example ===');

  await lilypad.span('parent-operation', async (parentSpan) => {
    parentSpan.info('Starting parent operation');

    // First child operation
    await lilypad.span('child-operation-1', async (childSpan) => {
      childSpan.info('Processing first child');
      await new Promise((resolve) => setTimeout(resolve, 50));
    });

    // Second child operation
    await lilypad.span('child-operation-2', async (childSpan) => {
      childSpan.info('Processing second child');
      await new Promise((resolve) => setTimeout(resolve, 50));
    });

    parentSpan.info('Parent operation completed');
  });
}

// Example 5: Error handling with spans
async function errorHandlingExample() {
  console.log('\n=== Error Handling Example ===');

  try {
    await lilypad.span('risky-operation', async (span) => {
      span.warning('Attempting risky operation');

      // Simulate an error condition
      const shouldFail = Math.random() > 0.5;

      if (shouldFail) {
        throw new Error('Operation failed randomly');
      }

      span.info('Operation succeeded');
    });
  } catch (error) {
    console.error('Caught error:', error);
  }
}

// Example 6: Using spans with sessions
async function sessionWithSpansExample() {
  console.log('\n=== Session with Spans Example ===');

  await lilypad.sessionAsync(async (session) => {
    console.log('Session ID:', session.id);

    await lilypad.span('session-operation-1', async (span) => {
      span.info('First operation in session');
      // The span will automatically have the session ID attached
    });

    await lilypad.span('session-operation-2', async (span) => {
      span.info('Second operation in session');
      // This span also has the same session ID
    });
  });
}

// Example 7: Using different log levels
async function logLevelsExample() {
  console.log('\n=== Log Levels Example ===');

  await lilypad.span('log-levels-demo', async (span) => {
    span.debug('Debug message - detailed information');
    span.info('Info message - general information');
    span.warning('Warning message - potential issue');

    // Error and critical will set the span status to ERROR
    span.error('Error message - something went wrong');
    span.critical('Critical message - severe issue');
  });
}

// Run all examples
async function runExamples() {
  try {
    await manualSpanExample();
    await asyncSpanExample();
    syncSpanExample();
    await nestedSpansExample();
    await errorHandlingExample();
    await sessionWithSpansExample();
    await logLevelsExample();

    console.log('\n=== All examples completed ===');

    // Shutdown to ensure all spans are exported
    await lilypad.shutdown();
  } catch (error) {
    console.error('Example failed:', error);
    process.exit(1);
  }
}

// Run the examples
runExamples();
