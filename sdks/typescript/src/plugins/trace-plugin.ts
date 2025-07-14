/**
 * Build-time plugin for extracting traced functions and their dependencies
 * Generates IIFE bundles for remote execution
 */

import * as esbuild from 'esbuild';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import * as crypto from 'node:crypto';
import { logger } from '../utils/logger';

export interface TracedFunctionMetadata {
  hash: string;
  name: string;
  signature: string;
  dependencies: string[];
  code: string;
  bundle: string;
  sourceFile: string;
  argTypes?: Record<string, string>;
  returnType?: string;
}

export interface TracePluginOptions {
  outputDir?: string;
  entryPoints?: string[];
  external?: string[];
  platform?: 'node' | 'browser';
}

/**
 * Analyze TypeScript/JavaScript code to find traced functions
 */
async function findTracedFunctions(filePath: string): Promise<string[]> {
  const content = await fs.readFile(filePath, 'utf-8');
  const tracedFunctions: string[] = [];
  
  // Simple regex to find @trace decorated functions
  // This is a simplified version - a proper implementation would use TypeScript AST
  const decoratorRegex = /@trace\s*\(\s*\{[^}]*versioning\s*:\s*['"]automatic['"]/g;
  const functionRegex = /(?:async\s+)?(?:function\s+)?(\w+)\s*\(/g;
  
  let match;
  while ((match = decoratorRegex.exec(content)) !== null) {
    // Find the next function after the decorator
    const afterDecorator = content.substring(match.index + match[0].length);
    const funcMatch = functionRegex.exec(afterDecorator);
    if (funcMatch && funcMatch[1]) {
      tracedFunctions.push(funcMatch[1]);
    }
  }
  
  return tracedFunctions;
}

/**
 * Generate IIFE bundle for a traced function
 */
async function generateBundle(
  functionName: string,
  sourceFile: string,
  options: TracePluginOptions,
): Promise<{ bundle: string; metafile: esbuild.Metafile }> {
  // Create a wrapper that exports only the traced function
  const wrapperContent = `
import * as __module from './${path.basename(sourceFile)}';

// Find the traced function
const tracedFunc = __module.${functionName} || __module.default?.${functionName};

if (!tracedFunc) {
  throw new Error('Traced function ${functionName} not found in module');
}

// Export as IIFE
globalThis.__lilypadFunction = tracedFunc;
`;

  const wrapperPath = path.join(
    path.dirname(sourceFile),
    `.lilypad-wrapper-${functionName}.js`
  );
  
  try {
    await fs.writeFile(wrapperPath, wrapperContent);
    
    // Build with esbuild
    const result = await esbuild.build({
      entryPoints: [wrapperPath],
      bundle: true,
      format: 'iife',
      platform: options.platform || 'node',
      target: 'es2020',
      minify: false,
      metafile: true,
      write: false,
      external: options.external || [],
      globalName: '__lilypadBundle',
      footer: {
        js: `
;(function() {
  if (typeof globalThis.__lilypadFunction === 'function') {
    globalThis.__lilypadExecute = globalThis.__lilypadFunction;
  }
})();`,
      },
    });
    
    return {
      bundle: result.outputFiles[0].text,
      metafile: result.metafile,
    };
  } finally {
    // Clean up wrapper file
    await fs.unlink(wrapperPath).catch(() => {});
  }
}

/**
 * Extract function metadata from source
 */
async function extractFunctionMetadata(
  functionName: string,
  sourceFile: string,
  bundle: string,
  metafile: esbuild.Metafile,
): Promise<TracedFunctionMetadata> {
  const content = await fs.readFile(sourceFile, 'utf-8');
  
  // Extract function signature (simplified - real implementation would use TS AST)
  const funcRegex = new RegExp(
    `(?:async\\s+)?(?:function\\s+)?${functionName}\\s*\\(([^)]*)\\)\\s*(?::\\s*([^{]+))?`,
    'g'
  );
  const match = funcRegex.exec(content);
  
  let signature = functionName;
  let returnType = 'any';
  
  if (match) {
    const params = match[1] || '';
    returnType = match[2]?.trim() || 'any';
    signature = `${functionName}(${params}): ${returnType}`;
  }
  
  // Extract dependencies from metafile
  const dependencies: string[] = [];
  for (const [inputFile, input] of Object.entries(metafile.inputs)) {
    for (const importPath of input.imports) {
      if (importPath.external && !dependencies.includes(importPath.path)) {
        dependencies.push(importPath.path);
      }
    }
  }
  
  // Calculate hash of the bundle
  const hash = crypto.createHash('sha256').update(bundle).digest('hex');
  
  // Extract the actual function code
  const functionCode = extractFunctionCode(content, functionName);
  
  return {
    hash,
    name: functionName,
    signature,
    dependencies,
    code: functionCode,
    bundle,
    sourceFile,
    returnType,
  };
}

/**
 * Extract function code from source
 */
function extractFunctionCode(content: string, functionName: string): string {
  // This is a simplified extraction - real implementation would use AST
  const funcRegex = new RegExp(
    `(@trace[^\\n]*\\n)?\\s*(?:export\\s+)?(?:async\\s+)?(?:function\\s+)?${functionName}\\s*\\([^)]*\\)\\s*(?::\\s*[^{]+)?\\s*\\{`,
    's'
  );
  
  const match = funcRegex.exec(content);
  if (!match) return '';
  
  let depth = 0;
  let i = match.index + match[0].length - 1;
  const start = match.index;
  
  // Find matching closing brace
  while (i < content.length) {
    if (content[i] === '{') depth++;
    else if (content[i] === '}') {
      depth--;
      if (depth === 0) {
        return content.substring(start, i + 1);
      }
    }
    i++;
  }
  
  return '';
}

/**
 * Create esbuild plugin for tracing
 */
export function createTracePlugin(options: TracePluginOptions = {}): esbuild.Plugin {
  return {
    name: 'lilypad-trace',
    setup(build) {
      build.onEnd(async (result) => {
        if (result.errors.length > 0) return;
        
        const outputDir = options.outputDir || path.join(process.cwd(), 'dist/trace-artifacts');
        await fs.mkdir(outputDir, { recursive: true });
        
        const metadata: Record<string, TracedFunctionMetadata> = {};
        
        // Process entry points
        const entryPoints = options.entryPoints || build.initialOptions.entryPoints || [];
        const processedFiles = new Set<string>();
        
        for (const entry of entryPoints) {
          const entryPath = typeof entry === 'string' ? entry : entry.in;
          if (!entryPath || processedFiles.has(entryPath)) continue;
          
          processedFiles.add(entryPath);
          
          try {
            // Find traced functions in the file
            const tracedFunctions = await findTracedFunctions(entryPath);
            
            for (const funcName of tracedFunctions) {
              logger.info(`Processing traced function: ${funcName} from ${entryPath}`);
              
              // Generate bundle
              const { bundle, metafile } = await generateBundle(funcName, entryPath, options);
              
              // Extract metadata
              const funcMetadata = await extractFunctionMetadata(
                funcName,
                entryPath,
                bundle,
                metafile
              );
              
              // Save bundle
              const bundlePath = path.join(outputDir, `${funcName}.bundle.js`);
              await fs.writeFile(bundlePath, bundle);
              
              metadata[funcName] = funcMetadata;
              
              logger.info(`Generated bundle for ${funcName}: ${bundlePath}`);
            }
          } catch (error) {
            logger.error(`Failed to process ${entryPath}:`, error);
          }
        }
        
        // Save metadata
        const metadataPath = path.join(outputDir, 'metadata.json');
        await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
        
        logger.info(`Trace plugin completed. Metadata saved to ${metadataPath}`);
      });
    },
  };
}

/**
 * Standalone build function for CLI usage
 */
export async function buildTracedFunctions(options: TracePluginOptions = {}): Promise<void> {
  const entryPoints = options.entryPoints || ['./src/**/*.ts'];
  const outputDir = options.outputDir || './dist/trace-artifacts';
  
  // For now, let's skip the actual build process and just create the output directory
  // The trace plugin will handle extraction when the files are processed
  await fs.mkdir(outputDir, { recursive: true });
  
  logger.info('Processing traced functions...');
  
  // Process each entry point file directly
  for (const entryPoint of entryPoints) {
    try {
      // Read the TypeScript file
      const sourceCode = await fs.readFile(entryPoint, 'utf-8');
      
      // Find traced functions using regex (simple approach for now)
      const tracedFunctionRegex = /@trace\s*\(\s*\{[^}]*versioning\s*:\s*['"]automatic['"]/g;
      const matches = sourceCode.match(tracedFunctionRegex);
      
      if (matches && matches.length > 0) {
        logger.info(`Found ${matches.length} traced function(s) in ${entryPoint}`);
        
        // For now, just create a placeholder metadata file
        const metadata = {
          [path.basename(entryPoint, '.ts')]: {
            source: entryPoint,
            tracedFunctions: matches.length,
            timestamp: new Date().toISOString(),
          }
        };
        
        const metadataPath = path.join(outputDir, 'metadata.json');
        await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
        
        logger.info(`Metadata saved to ${metadataPath}`);
      }
    } catch (error) {
      logger.error(`Failed to process ${entryPoint}:`, error);
    }
  }
  
  logger.info('Build completed. Note: Full traced function extraction requires running the TypeScript code.');
  logger.info('For production use, consider using: bun run examples/versioning.ts');
}

async function findJsFiles(dir: string): Promise<string[]> {
  const files: string[] = [];
  const entries = await fs.readdir(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await findJsFiles(fullPath));
    } else if (entry.name.endsWith('.js')) {
      files.push(fullPath);
    }
  }
  
  return files;
}