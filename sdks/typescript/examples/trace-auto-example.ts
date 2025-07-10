/**
 * TypeScript Example: Combining manual @trace with auto-instrumentation
 *
 * Run with:
 * npx tsx --require ./dist/register.js examples/trace-auto-example.ts
 */

import OpenAI from 'openai';
import { context, trace as otelTrace, SpanKind, Span } from '@opentelemetry/api';

// OpenAI client (automatically traced via auto-instrumentation)
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Helper function for manual tracing
function withTrace<T extends (...args: any[]) => any>(
  name: string,
  fn: T,
  options?: {
    attributes?: Record<string, any>;
    kind?: SpanKind;
  },
): T {
  return (async (...args: Parameters<T>): Promise<ReturnType<T>> => {
    const tracer = otelTrace.getTracer('lilypad');

    return tracer.startActiveSpan(
      name,
      {
        kind: options?.kind || SpanKind.INTERNAL,
        attributes: {
          'lilypad.type': 'trace',
          ...options?.attributes,
        },
      },
      async (span) => {
        try {
          const result = await fn(...args);
          span.setStatus({ code: 1 }); // OK
          return result;
        } catch (error) {
          span.recordException(error as Error);
          span.setStatus({ code: 2, message: String(error) });
          throw error;
        } finally {
          span.end();
        }
      },
    );
  }) as T;
}

// Get current span
function getCurrentSpan(): Span | undefined {
  return otelTrace.getActiveSpan();
}

// Add log to span
function logToSpan(level: string, message: string, attributes?: Record<string, any>) {
  const span = getCurrentSpan();
  if (span) {
    span.addEvent(`log.${level}`, {
      'log.message': message,
      ...attributes,
    });
  }
}

// Example 1: Question answering system
const answerQuestion = withTrace(
  'answerQuestion',
  async (question: string): Promise<string | null> => {
    // Business logic
    const normalizedQuestion = question.toLowerCase().trim();

    logToSpan('info', 'Processing question', {
      originalQuestion: question,
      normalizedQuestion,
    });

    // OpenAI API call (automatically traced)
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: `Answer this question: ${normalizedQuestion}` }],
    });

    return response.choices[0].message.content;
  },
);

// Example 2: Text translation
const translateText = withTrace(
  'translateText',
  async (text: string, targetLang: string): Promise<string> => {
    logToSpan('info', 'Starting translation', {
      sourceText: text,
      targetLanguage: targetLang,
      textLength: text.length,
    });

    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: `You are a translator. Translate the text to ${targetLang}. Return only the translation.`,
        },
        { role: 'user', content: text },
      ],
      temperature: 0.3,
    });

    const translation = response.choices[0].message.content || '';

    // Add custom attributes
    const span = getCurrentSpan();
    span?.setAttribute('translation.source.length', text.length);
    span?.setAttribute('translation.result.length', translation.length);
    span?.setAttribute('translation.targetLanguage', targetLang);

    return translation;
  },
);

// Example 3: Combining multiple AI features
const analyzeDocument = withTrace(
  'analyzeDocument',
  async (document: string) => {
    logToSpan('info', 'Starting document analysis', {
      documentLength: document.length,
    });

    // Parallel processing (each operation is recorded as a child span)
    const [summary, keywords, sentiment] = await Promise.all([
      summarizeText(document),
      extractKeywords(document),
      analyzeSentiment(document),
    ]);

    return {
      summary,
      keywords,
      sentiment,
      analyzedAt: new Date().toISOString(),
    };
  },
  {
    attributes: { 'analysis.type': 'comprehensive' },
  },
);

// Helper functions
const summarizeText = withTrace('summarizeText', async (text: string): Promise<string> => {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'system', content: 'Summarize the following text in 2-3 sentences.' },
      { role: 'user', content: text },
    ],
  });
  return response.choices[0].message.content || '';
});

const extractKeywords = withTrace('extractKeywords', async (text: string): Promise<string[]> => {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'system',
        content: 'Extract 3-5 important keywords and return them as a JSON array.',
      },
      { role: 'user', content: text },
    ],
  });

  try {
    return JSON.parse(response.choices[0].message.content || '[]');
  } catch {
    return [];
  }
});

const analyzeSentiment = withTrace('analyzeSentiment', async (text: string): Promise<string> => {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'system',
        content: 'Analyze the sentiment and return one of: positive, negative, or neutral.',
      },
      { role: 'user', content: text },
    ],
  });
  return response.choices[0].message.content || 'neutral';
});

// Main execution
async function main() {
  console.log('🚀 TypeScript: @trace + Auto-instrumentation Example\n');

  // Example 1: Question answering
  console.log('📝 Example 1: Question answering');
  const answer = await answerQuestion('What is TypeScript?');
  console.log('Answer:', answer);
  console.log();

  // Example 2: Translation
  console.log('🌐 Example 2: Text translation');
  const translation = await translateText('Hello, how are you today?', 'Spanish');
  console.log('Translation:', translation);
  console.log();

  // Example 3: Document analysis
  console.log('📊 Example 3: Document analysis');
  const document = `
    TypeScript is a programming language developed by Microsoft.
    It adds static typing to JavaScript and supports large-scale application development.
    Type safety helps catch bugs early and improves development efficiency.
  `;
  const analysis = await analyzeDocument(document);
  console.log('Analysis results:');
  console.log('  Summary:', analysis.summary);
  console.log('  Keywords:', analysis.keywords.join(', '));
  console.log('  Sentiment:', analysis.sentiment);
  console.log();

  console.log('📈 Trace hierarchy:');
  console.log('  └─ answerQuestion (manual trace)');
  console.log('     └─ OpenAI Chat Completion (auto trace)');
  console.log('  └─ translateText (manual trace)');
  console.log('     └─ OpenAI Chat Completion (auto trace)');
  console.log('  └─ analyzeDocument (manual trace)');
  console.log('     ├─ summarizeText (manual trace)');
  console.log('     │  └─ OpenAI Chat Completion (auto trace)');
  console.log('     ├─ extractKeywords (manual trace)');
  console.log('     │  └─ OpenAI Chat Completion (auto trace)');
  console.log('     └─ analyzeSentiment (manual trace)');
  console.log('        └─ OpenAI Chat Completion (auto trace)');
}

// Environment check
if (!process.env.OPENAI_API_KEY) {
  console.error('Error: OPENAI_API_KEY is not set');
  process.exit(1);
}

// Run
main().catch(console.error);
