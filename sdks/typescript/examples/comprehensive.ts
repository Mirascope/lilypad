/**
 * Comprehensive example demonstrating all major features of Lilypad TypeScript SDK
 * 
 * Features covered:
 * - Basic configuration
 * - @trace decorator (Bun) / wrapWithTrace (tsx)
 * - OpenAI integration
 * - Wrap mode with annotations
 * - Auto-instrumentation with --require flag
 */

import lilypad, { trace, wrapWithTrace } from '@lilypad/typescript-sdk';
import OpenAI from 'openai';

// Example 1: Using @trace decorator (works with Bun and tsx --tsconfig tsconfig.tsx.json)
class AIService {
  constructor(private client: OpenAI) {}

  @trace()
  async generateText(prompt: string): Promise<string | null> {
    const response = await this.client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 100,
    });
    return response.choices[0].message.content;
  }

  @trace({ mode: 'wrap', tags: ['analysis', 'complex'] })
  async analyzeText(text: string): Promise<any> {
    const response = await this.client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a text analyzer.' },
        { role: 'user', content: `Analyze this text: ${text}` }
      ],
    });
    return response.choices[0].message.content;
  }
}

// Example 2: Using wrapWithTrace (works everywhere, including tsx)
class DataProcessor {
  processData = wrapWithTrace(
    async (data: string): Promise<string> => {
      // Simulate processing
      await new Promise(resolve => setTimeout(resolve, 100));
      return data.toUpperCase();
    },
    { name: 'processData', tags: ['data-processing'] }
  );

  analyzeData = wrapWithTrace(
    async (data: any) => {
      // This returns a Trace object when mode is 'wrap'
      return {
        type: typeof data,
        length: JSON.stringify(data).length,
        timestamp: Date.now(),
      };
    },
    { mode: 'wrap', name: 'analyzeData' }
  );
}

async function main() {
  // Configure Lilypad SDK
  await lilypad.configure({
    apiKey: process.env.LILYPAD_API_KEY!,
    projectId: process.env.LILYPAD_PROJECT_ID!,
    baseUrl: process.env.LILYPAD_BASE_URL,
    remoteClientUrl: process.env.LILYPAD_REMOTE_CLIENT_URL,
    logLevel: 'info',
    // Enable auto-instrumentation for OpenAI (alternative to --require flag)
    // auto_llm: true,
  });

  console.log('=== Lilypad TypeScript SDK - Comprehensive Example ===\n');

  // Test data processor (no OpenAI dependency)
  console.log('1. Data Processing Example:');
  const processor = new DataProcessor();
  
  const processed = await processor.processData('hello world');
  console.log('Processed:', processed);

  // Test wrap mode with annotations
  const analysisTrace = await processor.analyzeData({ test: true, count: 42 });
  if (analysisTrace && 'response' in analysisTrace) {
    console.log('Analysis:', analysisTrace.response);
    
    // Add annotations (only available in wrap mode)
    try {
      await analysisTrace.annotate({
        label: 'pass',
        reasoning: 'Analysis completed successfully',
        type: 'automatic',
      });
      console.log('✅ Annotation added');
    } catch (error) {
      console.log('⚠️  Could not add annotation');
    }
  }

  // Test OpenAI integration (if API key available)
  if (process.env.OPENAI_API_KEY) {
    console.log('\n2. OpenAI Integration Example:');
    const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const aiService = new AIService(client);
    
    try {
      const text = await aiService.generateText('Write a haiku about coding');
      console.log('Generated:', text);
      
      const analysis = await aiService.analyzeText('The quick brown fox jumps over the lazy dog');
      if (analysis && 'response' in analysis) {
        console.log('Analysis:', analysis.response);
        // Can add annotations here too
      }
    } catch (error) {
      console.log('OpenAI error:', error instanceof Error ? error.message : error);
    }
  }

  console.log('\n📝 Usage Instructions:');
  console.log('\nFor Bun (native decorator support):');
  console.log('  bun run examples/comprehensive.ts');
  
  console.log('\nFor tsx (with custom config):');
  console.log('  npx tsx --tsconfig tsconfig.tsx.json examples/comprehensive.ts');
  
  console.log('\nFor auto-instrumentation (OpenAI calls automatically traced):');
  console.log('  npx tsx --require ./dist/register.js examples/comprehensive.ts');
  
  console.log('\n🔑 Environment Variables:');
  console.log('  LILYPAD_API_KEY=your-api-key');
  console.log('  LILYPAD_PROJECT_ID=your-project-id');
  console.log('  OPENAI_API_KEY=your-openai-key (optional)');

  // Shutdown
  await lilypad.shutdown();
}

// Check required environment variables
if (!process.env.LILYPAD_API_KEY || !process.env.LILYPAD_PROJECT_ID) {
  console.error('❌ Error: Please set LILYPAD_API_KEY and LILYPAD_PROJECT_ID');
  process.exit(1);
}

// Run the example
main().catch(console.error);