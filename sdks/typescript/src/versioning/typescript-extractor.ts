/**
 * TypeScript Code Extractor
 *
 * Extracts TypeScript source code at build time for versioned functions.
 * This allows users to see the original TypeScript code in the UI instead
 * of the compiled JavaScript.
 */

import ts from 'typescript';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

export interface ExtractedFunction {
  name: string;
  hash: string;
  sourceCode: string;
  signature: string;
  filePath: string;
  startLine: number;
  endLine: number;
  dependencies: Record<string, string>;
}

export interface VersioningMetadata {
  version: string;
  buildTime: string;
  functions: Record<string, ExtractedFunction>;
}

/**
 * Extract versioned functions from TypeScript source files
 */
export class TypeScriptExtractor {
  private program: ts.Program;
  private extractedFunctions: Map<string, ExtractedFunction> = new Map();

  constructor(
    private rootDir: string,
    tsConfigPath: string = 'tsconfig.json',
    private includePatterns: string[] = ['src/**/*.ts', 'examples/**/*.ts'],
  ) {
    // Parse tsconfig.json
    const configFile = ts.readConfigFile(path.join(rootDir, tsConfigPath), ts.sys.readFile);

    // Override the include patterns to include examples
    const config = {
      ...configFile.config,
      include: this.includePatterns,
      exclude: ['node_modules', 'dist', 'coverage', '**/*.test.ts', '**/*.spec.ts', 'lilypad/**'],
    };

    const parsedConfig = ts.parseJsonConfigFileContent(config, ts.sys, rootDir);

    // Create program
    this.program = ts.createProgram(parsedConfig.fileNames, parsedConfig.options);
  }

  /**
   * Extract all versioned functions from the project
   */
  extract(): VersioningMetadata {
    const sourceFiles = this.program.getSourceFiles();

    for (const sourceFile of sourceFiles) {
      // Skip node_modules and declaration files
      if (sourceFile.isDeclarationFile || sourceFile.fileName.includes('node_modules')) {
        continue;
      }

      this.visitNode(sourceFile);
    }

    return {
      version: '1.0.0',
      buildTime: new Date().toISOString(),
      functions: Object.fromEntries(this.extractedFunctions),
    };
  }

  /**
   * Visit AST nodes to find versioned functions
   */
  private visitNode(node: ts.Node): void {
    // Look for trace/wrapWithTrace calls with versioning
    if (ts.isCallExpression(node)) {
      const expression = node.expression;

      // Check if it's a trace or wrapWithTrace call
      if (
        ts.isIdentifier(expression) &&
        (expression.text === 'trace' || expression.text === 'wrapWithTrace')
      ) {
        this.handleTraceCall(node);
      }
    }

    // Recursively visit children
    ts.forEachChild(node, (child) => this.visitNode(child));
  }

  /**
   * Handle trace/wrapWithTrace function calls
   */
  private handleTraceCall(node: ts.CallExpression): void {
    const args = node.arguments;
    if (args.length < 1) return;

    // First argument should be the function
    const fnArg = args[0];

    // Second argument might be options
    const optionsArg = args[1];

    // Check if versioning is enabled
    if (!this.hasAutomaticVersioning(optionsArg)) {
      return;
    }

    // Extract the function source
    this.extractFunction(fnArg, node);
  }

  /**
   * Check if the options enable automatic versioning
   */
  private hasAutomaticVersioning(optionsNode?: ts.Expression): boolean {
    if (!optionsNode) return false;

    // Handle object literal { versioning: 'automatic' }
    if (ts.isObjectLiteralExpression(optionsNode)) {
      for (const prop of optionsNode.properties) {
        if (
          ts.isPropertyAssignment(prop) &&
          ts.isIdentifier(prop.name) &&
          prop.name.text === 'versioning'
        ) {
          const value = prop.initializer;
          if (ts.isStringLiteral(value) && value.text === 'automatic') {
            return true;
          }
        }
      }
    }

    return false;
  }

  /**
   * Extract function source code
   */
  private extractFunction(fnNode: ts.Expression, callNode: ts.CallExpression): void {
    const sourceFile = fnNode.getSourceFile();
    const sourceText = sourceFile.text;

    // Get function name
    let functionName = 'anonymous';
    if (ts.isFunctionExpression(fnNode) || ts.isArrowFunction(fnNode)) {
      // Try to get name from variable declaration
      const parent = callNode.parent;
      if (ts.isVariableDeclaration(parent) && ts.isIdentifier(parent.name)) {
        functionName = parent.name.text;
      } else if (fnNode.name) {
        functionName = fnNode.name.text;
      }
    }

    // Get the source code of the function
    const start = fnNode.getStart(sourceFile);
    const end = fnNode.getEnd();
    const sourceCode = sourceText.substring(start, end);

    // Get line numbers
    const startLine = sourceFile.getLineAndCharacterOfPosition(start).line + 1;
    const endLine = sourceFile.getLineAndCharacterOfPosition(end).line + 1;

    // Extract signature
    const signature = this.extractSignature(fnNode);

    // Extract dependencies (imports used in the function)
    const dependencies = this.extractDependencies(sourceFile, fnNode);

    // Generate hash
    const hash = crypto
      .createHash('sha256')
      .update(sourceCode)
      .update(JSON.stringify(dependencies))
      .digest('hex');

    // Store the extracted function
    const extractedFn: ExtractedFunction = {
      name: functionName,
      hash,
      sourceCode,
      signature,
      filePath: path.relative(this.rootDir, sourceFile.fileName),
      startLine,
      endLine,
      dependencies,
    };

    this.extractedFunctions.set(hash, extractedFn);
  }

  /**
   * Extract function signature
   */
  private extractSignature(fnNode: ts.Expression): string {
    if (ts.isFunctionExpression(fnNode) || ts.isArrowFunction(fnNode)) {
      const params = fnNode.parameters.map((p) => p.getText()).join(', ');
      const isAsync = fnNode.modifiers?.some((m) => m.kind === ts.SyntaxKind.AsyncKeyword) ?? false;

      if (ts.isArrowFunction(fnNode)) {
        return `${isAsync ? 'async ' : ''}(${params}) => ...`;
      } else {
        const name = fnNode.name?.text || 'function';
        return `${isAsync ? 'async ' : ''}function ${name}(${params})`;
      }
    }

    return 'function()';
  }

  /**
   * Extract dependencies (simplified - just module names for now)
   */
  private extractDependencies(
    sourceFile: ts.SourceFile,
    _fnNode: ts.Expression,
  ): Record<string, string> {
    const dependencies: Record<string, string> = {};

    // Find all import declarations in the file
    sourceFile.statements.forEach((statement) => {
      if (ts.isImportDeclaration(statement)) {
        const moduleSpecifier = statement.moduleSpecifier;
        if (ts.isStringLiteral(moduleSpecifier)) {
          const moduleName = moduleSpecifier.text;
          // For now, just track that the module is imported
          // In a real implementation, we'd check if symbols from this
          // module are actually used in the function
          dependencies[moduleName] = '*';
        }
      }
    });

    return dependencies;
  }

  /**
   * Save metadata to file
   */
  saveMetadata(outputPath: string): void {
    const metadata = this.extract();
    const outputDir = path.dirname(outputPath);

    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));
  }
}

/**
 * CLI interface for the extractor
 */
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: ts-node typescript-extractor.ts <project-root> [output-path]');
    process.exit(1);
  }

  const rootDir = args[0];
  const outputPath = args[1] || path.join(rootDir, 'versioning-metadata.json');

  console.log(`Extracting versioned functions from: ${rootDir}`);

  const extractor = new TypeScriptExtractor(rootDir);
  extractor.saveMetadata(outputPath);

  console.log(`Metadata saved to: ${outputPath}`);
}
