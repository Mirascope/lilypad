/**
 * Example: Using trace decorator with wrap mode
 * 
 * This example demonstrates how to use the `mode: 'wrap'` option with the trace decorator
 * to get a Trace object that allows post-execution operations like annotation, assignment, and tagging.
 */

import { configure, trace, Trace, AsyncTrace } from '@lilypad/typescript-sdk';

// Configure the SDK
configure({
  apiKey: process.env.LILYPAD_API_KEY!,
  projectId: process.env.LILYPAD_PROJECT_ID!,
});

// Example 1: Synchronous function with wrap mode
class DataProcessor {
  @trace({ mode: 'wrap', tags: ['production', 'data-processing'] })
  processData(input: string): string {
    // Simulate some data processing
    const processed = input.toUpperCase().replace(/\s+/g, '_');
    return `PROCESSED_${processed}`;
  }
}

// Example 2: Asynchronous function with wrap mode
class AIService {
  @trace({ mode: 'wrap', name: 'ai_inference' })
  async generateResponse(prompt: string): Promise<{ text: string; confidence: number }> {
    // Simulate AI processing
    await new Promise((resolve) => setTimeout(resolve, 100));
    
    return {
      text: `Response to: ${prompt}`,
      confidence: 0.95,
    };
  }
}

// Example 3: Error handling with wrap mode
class ValidationService {
  @trace({ mode: 'wrap' })
  validateInput(data: any): boolean {
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid input: expected object');
    }
    return true;
  }
}

async function runExamples() {
  console.log('=== Trace Wrap Mode Examples ===\n');

  // Example 1: Using synchronous trace with annotations
  console.log('1. Synchronous function with wrap mode:');
  const processor = new DataProcessor();
  const result1 = processor.processData('hello world');
  
  // result1 is a Trace object, not the raw result
  console.log('Result type:', result1.constructor.name); // "Trace"
  console.log('Actual result:', result1.response); // "PROCESSED_HELLO_WORLD"
  
  // Add annotation to the trace
  result1.annotate({
    label: 'pass',
    reasoning: 'Data processed successfully',
    type: 'manual',
    data: { input_length: 11, output_length: result1.response.length },
  });
  
  // Add tags to the trace
  result1.tag('successful', 'text-processing');
  
  console.log('Annotations and tags added to trace\n');

  // Example 2: Using asynchronous trace with multiple annotations
  console.log('2. Asynchronous function with wrap mode:');
  const aiService = new AIService();
  const result2 = await aiService.generateResponse('What is the weather?');
  
  // result2 is an AsyncTrace object
  console.log('Result type:', result2.constructor.name); // "AsyncTrace"
  console.log('AI Response:', result2.response);
  
  // Add multiple annotations
  await result2.annotate(
    {
      label: 'pass',
      type: 'automatic',
      data: { model: 'gpt-4', temperature: 0.7 },
    },
    {
      label: result2.response.confidence > 0.9 ? 'pass' : 'fail',
      reasoning: `Confidence level: ${result2.response.confidence}`,
      type: 'automatic',
    },
  );
  
  // Assign to team members for review
  await result2.assign('reviewer@example.com', 'qa@example.com');
  
  console.log('Annotations and assignments added to async trace\n');

  // Example 3: Error handling
  console.log('3. Error handling with wrap mode:');
  const validator = new ValidationService();
  
  try {
    const result3 = validator.validateInput(null);
    // This won't execute due to error
  } catch (error) {
    console.log('Validation failed:', error.message);
    // The trace is still recorded with error status
  }

  // Example 4: Working with complex return types
  console.log('\n4. Complex return types:');
  
  class ReportGenerator {
    @trace({ mode: 'wrap', name: 'generate_monthly_report' })
    async generateReport(month: string): Promise<{
      summary: string;
      data: number[];
      metadata: Record<string, any>;
    }> {
      await new Promise((resolve) => setTimeout(resolve, 50));
      
      return {
        summary: `Report for ${month}`,
        data: [100, 200, 150, 300],
        metadata: {
          generated_at: new Date().toISOString(),
          version: '1.0',
        },
      };
    }
  }

  const reportGen = new ReportGenerator();
  const reportTrace = await reportGen.generateReport('January');
  
  // Access the actual report data
  const report = reportTrace.response;
  console.log('Report summary:', report.summary);
  console.log('Total data points:', report.data.length);
  
  // Annotate based on report contents
  await reportTrace.annotate({
    label: report.data.every((v) => v > 0) ? 'pass' : 'fail',
    reasoning: 'All data points are positive',
    type: 'automatic',
    data: {
      total: report.data.reduce((a, b) => a + b, 0),
      average: report.data.reduce((a, b) => a + b, 0) / report.data.length,
    },
  });

  console.log('\n=== Examples completed ===');
}

// Run the examples
runExamples().catch(console.error);