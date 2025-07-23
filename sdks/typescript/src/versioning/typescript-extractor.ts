/**
 * Extracts TypeScript source code at build time for versioned functions.
 */

import ts from 'typescript';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { Project } from 'ts-morph';
import { DependencyExtractor } from './dependency-extractor';

export interface ExtractedFunction {
  name: string;
  hash: string;
  sourceCode: string;
  signature: string;
  filePath: string;
  startLine: number;
  endLine: number;
  dependencies: Record<string, string>;
  selfContainedCode?: string; // Complete executable code with dependencies
}

export interface VersioningMetadata {
  version: string;
  buildTime: string;
  functions: Record<string, ExtractedFunction>;
}

export class TypeScriptExtractor {
  private program: ts.Program;
  private extractedFunctions: Map<string, ExtractedFunction> = new Map();
  private dependencyExtractor: DependencyExtractor | null = null;
  private tsMorphProject: Project | null = null;

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

    // Initialize ts-morph for dependency extraction
    try {
      console.log('Initializing dependency extractor...');
      this.dependencyExtractor = new DependencyExtractor(path.join(rootDir, tsConfigPath));
      this.tsMorphProject = new Project({
        tsConfigFilePath: path.join(rootDir, tsConfigPath),
        skipAddingFilesFromTsConfig: true, // We'll add files manually
      });

      // Add the same files that the TypeScript compiler is using
      console.log(`Adding ${parsedConfig.fileNames.length} files to ts-morph project...`);
      for (const fileName of parsedConfig.fileNames) {
        try {
          this.tsMorphProject.addSourceFileAtPath(fileName);
        } catch (err) {
          // Skip files that can't be added
          console.warn(`Failed to add file ${fileName} to ts-morph project:`, err as Error);
        }
      }

      console.log('Dependency extractor initialized successfully');
    } catch (error) {
      console.warn('Failed to initialize dependency extractor:', error);
    }
  }

  extract(): VersioningMetadata {
    const sourceFiles = this.program.getSourceFiles();

    for (const sourceFile of sourceFiles) {
      // Skip node_modules and declaration files
      if (sourceFile.isDeclarationFile || sourceFile.fileName.includes('node_modules')) {
        continue;
      }

      try {
        this.visitNode(sourceFile, sourceFile);
      } catch (error) {
        console.warn(`Error processing file ${sourceFile.fileName}:`, error);
      }
    }

    return {
      version: '1.0.0',
      buildTime: new Date().toISOString(),
      functions: Object.fromEntries(this.extractedFunctions),
    };
  }

  private visitNode(node: ts.Node, sourceFile: ts.SourceFile): void {
    // Look for trace/wrapWithTrace calls with versioning
    if (ts.isCallExpression(node)) {
      const expression = node.expression;

      if (
        ts.isIdentifier(expression) &&
        (expression.text === 'trace' || expression.text === 'wrapWithTrace')
      ) {
        this.handleTraceCall(node, sourceFile);
      }
    }

    // Recursively visit children
    ts.forEachChild(node, (child) => this.visitNode(child, sourceFile));
  }

  private handleTraceCall(node: ts.CallExpression, sourceFile: ts.SourceFile): void {
    const args = node.arguments;
    if (args.length < 1) return;

    // First argument should be the function
    const fnArg = args[0];

    // Second argument might be options
    const optionsArg = args[1];

    if (!this.hasAutomaticVersioning(optionsArg)) {
      return;
    }

    this.extractFunction(fnArg, node, sourceFile, optionsArg);
  }

  private hasAutomaticVersioning(optionsNode?: ts.Expression): boolean {
    if (!optionsNode) return false;

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

  private extractFunction(
    fnNode: ts.Expression,
    callNode: ts.CallExpression,
    sourceFile: ts.SourceFile,
    optionsNode?: ts.Expression,
  ): void {
    const sourceText = sourceFile.text;
    if (!sourceText) {
      console.warn('Source text not available for file:', sourceFile.fileName);
      return;
    }

    let functionName = 'anonymous';

    // First, try to get name from options
    if (optionsNode && ts.isObjectLiteralExpression(optionsNode)) {
      for (const prop of optionsNode.properties) {
        if (
          ts.isPropertyAssignment(prop) &&
          ts.isIdentifier(prop.name) &&
          prop.name.text === 'name'
        ) {
          const value = prop.initializer;
          if (ts.isStringLiteral(value)) {
            functionName = value.text;
            break;
          }
        }
      }
    }

    // If no name in options, try to get from variable declaration
    if (functionName === 'anonymous') {
      // Traverse up to find variable declaration
      let parent: ts.Node | undefined = callNode.parent;
      while (parent) {
        if (ts.isVariableDeclaration(parent) && ts.isIdentifier(parent.name)) {
          functionName = parent.name.text;
          break;
        }
        parent = parent.parent;
      }

      // Try function name if it's a named function expression
      if (functionName === 'anonymous' && ts.isFunctionExpression(fnNode) && fnNode.name) {
        functionName = fnNode.name.text;
      }
    }

    const start = fnNode.getStart(sourceFile);
    const end = fnNode.getEnd();
    const sourceCode = sourceText.substring(start, end);

    const startLine = sourceFile.getLineAndCharacterOfPosition(start).line + 1;
    const endLine = sourceFile.getLineAndCharacterOfPosition(end).line + 1;

    const signature = this.extractSignature(fnNode, sourceFile);

    const dependencies = this.extractDependencies(sourceFile, fnNode);

    let selfContainedCode: string | undefined;
    console.log(`Attempting to extract self-contained code for ${functionName}...`);
    console.log(`DependencyExtractor available: ${!!this.dependencyExtractor}`);
    console.log(`TsMorphProject available: ${!!this.tsMorphProject}`);

    if (this.dependencyExtractor && this.tsMorphProject) {
      try {
        const tsMorphFile = this.tsMorphProject.getSourceFile(sourceFile.fileName);
        console.log(`TsMorph file found: ${!!tsMorphFile}, fileName: ${sourceFile.fileName}`);
        if (tsMorphFile) {
          console.log(`Looking for function at positions: start=${start}, end=${end}`);
          console.log(`Function code preview: ${sourceCode.substring(0, 100)}...`);
          const tsMorphFunction = this.findCorrespondingFunctionByCode(tsMorphFile, sourceCode);
          console.log(`TsMorph function found: ${!!tsMorphFunction}`);
          if (tsMorphFunction) {
            const extracted = this.dependencyExtractor.extractFunctionWithDependencies(
              tsMorphFile,
              tsMorphFunction,
            );
            selfContainedCode = extracted.selfContainedCode;
            console.log(`Self-contained code extracted, length: ${selfContainedCode?.length}`);
          }
        }
      } catch (error) {
        console.warn('Failed to extract self-contained code:', error);
      }
    }

    // Generate hash from self-contained code if available, otherwise from source
    const hashSource = selfContainedCode || sourceCode;
    const hash = crypto
      .createHash('sha256')
      .update(hashSource)
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
      selfContainedCode,
    };

    this.extractedFunctions.set(hash, extractedFn);
  }

  private extractSignature(fnNode: ts.Expression, sourceFile: ts.SourceFile): string {
    if (ts.isFunctionExpression(fnNode) || ts.isArrowFunction(fnNode)) {
      const params = fnNode.parameters.map((p) => p.getText(sourceFile)).join(', ');
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

  private extractDependencies(
    sourceFile: ts.SourceFile,
    _fnNode: ts.Expression,
  ): Record<string, string> {
    const dependencies: Record<string, string> = {};

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

  private findCorrespondingFunctionByCode(
    sourceFile: any, // ts-morph SourceFile
    targetCode: string,
  ): any {
    // Import dynamically to avoid circular dependency
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { Node, SyntaxKind } = require('ts-morph');

    // Normalize the target code for comparison
    const normalizedTarget = targetCode.replace(/\s+/g, ' ').trim();
    console.log(`Looking for function with normalized code length: ${normalizedTarget.length}`);

    // Try to get all functions using different methods
    const functionDeclarations = sourceFile.getFunctions();
    console.log(`  Found ${functionDeclarations.length} function declarations`);

    // Also look for arrow functions and function expressions
    const allFunctions: any[] = [...functionDeclarations];

    sourceFile.getDescendantsOfKind(SyntaxKind.VariableDeclaration).forEach((varDecl: any) => {
      const initializer = varDecl.getInitializer();
      if (
        initializer &&
        (Node.isArrowFunction(initializer) || Node.isFunctionExpression(initializer))
      ) {
        allFunctions.push(initializer);
      }
    });

    sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression).forEach((callExpr: any) => {
      const expression = callExpr.getExpression();
      if (
        Node.isIdentifier(expression) &&
        (expression.getText() === 'trace' || expression.getText() === 'wrapWithTrace')
      ) {
        const args = callExpr.getArguments();
        if (args.length > 0) {
          const firstArg = args[0];
          if (Node.isArrowFunction(firstArg) || Node.isFunctionExpression(firstArg)) {
            allFunctions.push(firstArg);
          }
        }
      }
    });

    console.log(`  Total functions found (all types): ${allFunctions.length}`);

    let foundFunction: any = null;
    let bestMatch: any = null;
    let bestScore = 0;

    allFunctions.forEach((func, index) => {
      const nodeText = func.getText().replace(/\s+/g, ' ').trim();

      // Debug first few functions
      if (index < 3) {
        console.log(
          `  Function ${index + 1}: ${func.getKindName ? func.getKindName() : 'Unknown'}`,
        );
        console.log(`    Code length: ${nodeText.length}`);
        console.log(`    Code preview: ${nodeText.substring(0, 60)}...`);
      }

      // First, try exact match (after normalization)
      if (nodeText === normalizedTarget) {
        console.log(`  Found exact match by normalized text!`);
        foundFunction = func;
        return;
      }

      const score = this.calculateSimilarityScore(normalizedTarget, nodeText);
      if (score > bestScore) {
        bestMatch = func;
        bestScore = score;
        if (score > 0.8) {
          // Lower threshold for debugging
          console.log(`  Found potential match with score: ${score}`);
        }
      }
    });

    console.log(`  Best match score: ${bestScore}`);

    return foundFunction || (bestScore > 0.8 ? bestMatch : null);
  }

  private calculateSimilarityScore(str1: string, str2: string): number {
    // Normalize whitespace for comparison
    const norm1 = str1.replace(/\s+/g, ' ').trim();
    const norm2 = str2.replace(/\s+/g, ' ').trim();

    // Quick checks
    if (norm1 === norm2) return 1;
    if (norm1.length === 0 || norm2.length === 0) return 0;

    const maxLen = Math.max(norm1.length, norm2.length);
    const distance = this.levenshteinDistance(norm1, norm2);
    return 1 - distance / maxLen;
  }

  private levenshteinDistance(str1: string, str2: string): number {
    const matrix: number[][] = [];

    // Initialize matrix
    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }
    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    // Fill matrix
    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1, // substitution
            matrix[i][j - 1] + 1, // insertion
            matrix[i - 1][j] + 1, // deletion
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  saveMetadata(outputPath: string): void {
    const metadata = this.extract();
    const outputDir = path.dirname(outputPath);

    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(metadata, null, 2));
  }
}

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
