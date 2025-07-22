/**
 * TypeScript Dependency Extractor
 *
 * Similar to Python's Closure class, this extracts not just the function code
 * but also all its dependencies to create self-contained code blocks.
 */

import {
  Project,
  Node,
  SyntaxKind,
  SourceFile,
  FunctionDeclaration,
  FunctionExpression,
  ArrowFunction,
  Identifier,
} from 'ts-morph';
import * as path from 'path';
import * as crypto from 'crypto';

export interface ExtractedDependency {
  name: string;
  code: string;
  type: 'function' | 'class' | 'variable' | 'type' | 'interface';
  source?: string; // module it was imported from
}

export interface SelfContainedFunction {
  name: string;
  hash: string;
  code: string; // The main function code
  dependencies: ExtractedDependency[];
  imports: string[]; // Required import statements
  selfContainedCode: string; // Complete executable code
}

export class DependencyExtractor {
  private project: Project;
  private visitedNodes = new Set<Node>();

  constructor(tsConfigPath: string) {
    this.project = new Project({
      tsConfigFilePath: tsConfigPath,
      skipAddingFilesFromTsConfig: false,
    });
  }

  /**
   * Extract a function and all its dependencies to create self-contained code
   */
  extractFunctionWithDependencies(
    sourceFile: SourceFile,
    functionNode: FunctionDeclaration | FunctionExpression | ArrowFunction,
  ): SelfContainedFunction {
    this.visitedNodes.clear();

    // Get function name
    const functionName = this.getFunctionName(functionNode);

    // Extract the main function code
    const functionCode = functionNode.getText();

    // Find all identifiers used in the function
    const identifiers = this.findIdentifiersInFunction(functionNode);

    // Resolve dependencies for each identifier
    const dependencies: ExtractedDependency[] = [];
    const imports = new Set<string>();
    const processedDeps = new Set<string>();

    // Queue for processing dependencies recursively
    const identifiersToProcess = [...identifiers];
    
    while (identifiersToProcess.length > 0) {
      const identifier = identifiersToProcess.shift()!;
      const dep = this.resolveDependency(identifier, sourceFile);
      
      if (dep && !processedDeps.has(dep.name)) {
        processedDeps.add(dep.name);
        dependencies.push(dep);

        // If it's an external import, track it
        if (dep.source) {
          imports.add(`import { ${dep.name} } from '${dep.source}';`);
        }
        
        // For functions and variables, find their dependencies too
        if (dep.type === 'function' || dep.type === 'variable') {
          const depNode = this.findNodeByCode(sourceFile, dep.code);
          if (depNode) {
            const depIdentifiers = this.findIdentifiersInFunction(depNode);
            // Add new identifiers that haven't been processed
            for (const depId of depIdentifiers) {
              const depName = depId.getText();
              if (!processedDeps.has(depName)) {
                identifiersToProcess.push(depId);
              }
            }
          }
        }
      }
    }

    // Build self-contained code
    const selfContainedCode = this.buildSelfContainedCode(
      functionName,
      functionCode,
      dependencies,
      Array.from(imports),
    );

    // Generate hash from self-contained code
    const hash = crypto.createHash('sha256').update(selfContainedCode).digest('hex');

    return {
      name: functionName,
      hash,
      code: functionCode,
      dependencies,
      imports: Array.from(imports),
      selfContainedCode,
    };
  }

  /**
   * Get the name of a function node
   */
  private getFunctionName(node: FunctionDeclaration | FunctionExpression | ArrowFunction): string {
    if (Node.isFunctionDeclaration(node) && node.getName()) {
      return node.getName() || 'anonymous';
    }

    // Check if it's assigned to a variable
    const parent = node.getParent();
    if (Node.isVariableDeclaration(parent)) {
      return parent.getName();
    }

    return 'anonymous';
  }

  /**
   * Find all identifiers used within a function
   */
  private findIdentifiersInFunction(functionNode: Node): Identifier[] {
    const identifiers: Identifier[] = [];
    const localVariables = new Set<string>();

    // First pass: collect local variable declarations
    functionNode.forEachDescendant((node) => {
      if (Node.isVariableDeclaration(node)) {
        localVariables.add(node.getName());
      } else if (Node.isParameterDeclaration && Node.isParameterDeclaration(node)) {
        localVariables.add(node.getName ? node.getName() : '');
      }
    });

    // Second pass: collect non-local identifiers
    functionNode.forEachDescendant((node) => {
      if (Node.isIdentifier(node) && !this.isDeclaration(node)) {
        const name = node.getText();

        // Skip local variables, built-ins, and 'this'
        if (
          !localVariables.has(name) &&
          !this.isBuiltIn(name) &&
          name !== 'this' &&
          name !== 'super' &&
          name !== 'undefined' &&
          name !== 'null'
        ) {
          identifiers.push(node);
        }
      }
    });

    return identifiers;
  }

  /**
   * Check if an identifier is a declaration (not a usage)
   */
  private isDeclaration(identifier: Identifier): boolean {
    const parent = identifier.getParent();

    // Variable declaration
    if (Node.isVariableDeclaration(parent) && parent.getNameNode() === identifier) {
      return true;
    }

    // Function declaration
    if (Node.isFunctionDeclaration(parent) && parent.getNameNode() === identifier) {
      return true;
    }

    // Parameter
    if (Node.isParameterDeclaration && Node.isParameterDeclaration(parent)) {
      // Check if this identifier is the parameter name
      try {
        const nameNode = parent.getFirstChildByKind
          ? parent.getFirstChildByKind(SyntaxKind.Identifier)
          : null;
        if (nameNode === identifier) {
          return true;
        }
      } catch {
        // Some nodes may not have this method
      }
    }

    // Property declaration
    if (Node.isPropertyDeclaration(parent) && parent.getNameNode() === identifier) {
      return true;
    }

    return false;
  }

  /**
   * Find a node in the source file by its code
   */
  private findNodeByCode(sourceFile: SourceFile, code: string): Node | null {
    const normalizedCode = code.replace(/\s+/g, ' ').trim();
    
    // Try to find the node with matching text
    const result = sourceFile.forEachDescendant((node) => {
      const nodeText = node.getText().replace(/\s+/g, ' ').trim();
      if (nodeText === normalizedCode) {
        return node;
      }
      return undefined;
    });
    
    return result || null;
  }

  /**
   * Check if an identifier is a built-in
   */
  private isBuiltIn(name: string): boolean {
    const builtIns = new Set([
      'console',
      'process',
      'global',
      'window',
      'document',
      'Array',
      'Object',
      'String',
      'Number',
      'Boolean',
      'Date',
      'Math',
      'JSON',
      'Promise',
      'Map',
      'Set',
      'RegExp',
      'Error',
      'TypeError',
      'SyntaxError',
      'ReferenceError',
      'parseInt',
      'parseFloat',
      'isNaN',
      'isFinite',
      'setTimeout',
      'setInterval',
      'clearTimeout',
      'clearInterval',
      'require',
      'exports',
      'module',
      '__dirname',
      '__filename',
    ]);

    return builtIns.has(name);
  }

  /**
   * Resolve a dependency for an identifier
   */
  private resolveDependency(
    identifier: Identifier,
    sourceFile: SourceFile,
  ): ExtractedDependency | null {
    const name = identifier.getText();
    const symbol = identifier.getSymbol();

    if (!symbol) {
      return null;
    }

    // Get the declaration
    const declarations = symbol.getDeclarations();
    if (!declarations || declarations.length === 0) {
      return null;
    }

    const declaration = declarations[0];

    // Skip if already visited (prevent infinite recursion)
    if (this.visitedNodes.has(declaration)) {
      return null;
    }
    this.visitedNodes.add(declaration);

    // Handle different types of declarations
    if (Node.isFunctionDeclaration(declaration)) {
      return {
        name,
        code: declaration.getText(),
        type: 'function',
      };
    }

    if (Node.isVariableDeclaration(declaration)) {
      const statement = declaration.getVariableStatement();
      if (statement) {
        const initializer = declaration.getInitializer();
        if (
          initializer &&
          (Node.isFunctionExpression(initializer) || Node.isArrowFunction(initializer))
        ) {
          return {
            name,
            code: statement.getText(),
            type: 'function',
          };
        }
        return {
          name,
          code: statement.getText(),
          type: 'variable',
        };
      }
    }

    if (Node.isClassDeclaration(declaration)) {
      return {
        name,
        code: declaration.getText(),
        type: 'class',
      };
    }

    if (Node.isInterfaceDeclaration(declaration) || Node.isTypeAliasDeclaration(declaration)) {
      return {
        name,
        code: declaration.getText(),
        type: Node.isInterfaceDeclaration(declaration) ? 'interface' : 'type',
      };
    }

    // Handle imports
    if (Node.isImportSpecifier(declaration) || Node.isImportClause(declaration)) {
      const importDecl = declaration.getFirstAncestorByKind(SyntaxKind.ImportDeclaration);
      if (importDecl) {
        const moduleSpecifier = importDecl.getModuleSpecifierValue();

        // If it's a relative import, try to follow it
        if (moduleSpecifier.startsWith('.')) {
          const importedFile = this.resolveImportedFile(sourceFile, moduleSpecifier);
          if (importedFile) {
            // Find the exported declaration in the imported file
            const exportedDecl = this.findExportedDeclaration(importedFile, name);
            if (exportedDecl) {
              const dep = this.resolveDependency(exportedDecl, importedFile);
              if (dep) {
                dep.source = moduleSpecifier;
                return dep;
              }
            }
          }
        } else {
          // External module
          return {
            name,
            code: '', // External modules don't have code
            type: 'function', // Assume function for now
            source: moduleSpecifier,
          };
        }
      }
    }

    return null;
  }

  /**
   * Resolve an imported file path
   */
  private resolveImportedFile(currentFile: SourceFile, importPath: string): SourceFile | null {
    const currentDir = path.dirname(currentFile.getFilePath());
    const possiblePaths = [
      path.join(currentDir, importPath + '.ts'),
      path.join(currentDir, importPath + '.tsx'),
      path.join(currentDir, importPath, 'index.ts'),
      path.join(currentDir, importPath, 'index.tsx'),
    ];

    for (const filePath of possiblePaths) {
      const sourceFile = this.project.getSourceFile(filePath);
      if (sourceFile) {
        return sourceFile;
      }
    }

    return null;
  }

  /**
   * Find an exported declaration by name
   */
  private findExportedDeclaration(sourceFile: SourceFile, name: string): Identifier | null {
    // Check named exports
    const exportedDeclarations = sourceFile.getExportedDeclarations();
    const exported = exportedDeclarations.get(name);
    if (exported && exported.length > 0) {
      const decl = exported[0];
      if (Node.isIdentifier(decl)) {
        return decl;
      }
      // Try to find the identifier in the declaration
      const identifier = decl.getFirstDescendantByKind(SyntaxKind.Identifier);
      if (identifier && identifier.getText() === name) {
        return identifier;
      }
    }

    // Check default export
    const defaultExport = sourceFile.getDefaultExportSymbol();
    if (defaultExport && defaultExport.getName() === name) {
      const declarations = defaultExport.getDeclarations();
      if (declarations.length > 0) {
        const identifier = declarations[0].getFirstDescendantByKind(SyntaxKind.Identifier);
        if (identifier) {
          return identifier;
        }
      }
    }

    return null;
  }

  /**
   * Build self-contained code from function and dependencies
   */
  private buildSelfContainedCode(
    _functionName: string,
    functionCode: string,
    dependencies: ExtractedDependency[],
    imports: string[],
  ): string {
    const parts: string[] = [];

    // Add imports for external dependencies
    const externalImports = imports.filter((imp) => !imp.includes('./'));
    if (externalImports.length > 0) {
      parts.push('// External imports');
      parts.push(...externalImports);
      parts.push('');
    }

    // Add type/interface dependencies first
    const typeDeps = dependencies.filter((d) => d.type === 'type' || d.type === 'interface');
    if (typeDeps.length > 0) {
      parts.push('// Type dependencies');
      typeDeps.forEach((dep) => {
        if (dep.code) {
          parts.push(dep.code);
        }
      });
      parts.push('');
    }

    // Add variable/class dependencies
    const varClassDeps = dependencies.filter((d) => d.type === 'variable' || d.type === 'class');
    if (varClassDeps.length > 0) {
      parts.push('// Variable and class dependencies');
      varClassDeps.forEach((dep) => {
        if (dep.code) {
          parts.push(dep.code);
        }
      });
      parts.push('');
    }

    // Add function dependencies
    const funcDeps = dependencies.filter((d) => d.type === 'function' && d.code);
    if (funcDeps.length > 0) {
      parts.push('// Function dependencies');
      funcDeps.forEach((dep) => {
        if (dep.code) {
          parts.push(dep.code);
        }
      });
      parts.push('');
    }

    // Add the main function
    parts.push('// Main function');
    parts.push(functionCode);

    return parts.join('\n');
  }
}
