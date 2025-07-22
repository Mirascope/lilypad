/**
 * Versioning Metadata Loader
 *
 * Loads and manages TypeScript source code metadata extracted at build time.
 * This allows the SDK to use the original TypeScript code instead of
 * runtime JavaScript code.
 */

import { logger } from '../utils/logger';
import type { ExtractedFunction, VersioningMetadata } from './typescript-extractor';

class MetadataLoader {
  private metadata: VersioningMetadata | null = null;
  private functionsByHash: Map<string, ExtractedFunction> = new Map();
  private functionsByName: Map<string, ExtractedFunction> = new Map();
  private loaded = false;

  /**
   * Load metadata from file system (Node.js) or bundled data
   */
  load(): void {
    if (this.loaded) return;

    try {
      // Check if we're in Node.js environment
      if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        // Node.js environment - try to load from file system
        this.loadFromFileSystem();
      } else {
        // Browser or other environment - metadata should be bundled
        this.loadFromBundle();
      }

      this.loaded = true;
    } catch (error) {
      logger.error('Failed to load versioning metadata:', error);
      this.loaded = true;
    }
  }

  /**
   * Load metadata from file system (Node.js only)
   */
  private loadFromFileSystem(): void {
    try {
      // Dynamic imports to avoid bundling fs/path in browser builds
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const fs = require('fs');
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const path = require('path');

      // Try multiple locations for the metadata file
      const possiblePaths = [
        // Production: in dist folder
        path.join(__dirname, '../../dist/versioning-metadata.json'),
        // Development: in src folder
        path.join(__dirname, './metadata.json'),
        // Alternative: root of the package
        path.join(process.cwd(), 'versioning-metadata.json'),
        // Example projects
        path.join(process.cwd(), 'lilypad-metadata.json'),
        // Bundled with dist
        path.join(__dirname, '../versioning-metadata.json'),
      ];

      logger.debug('Searching for metadata in:', possiblePaths);

      let metadataPath: string | null = null;
      for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
          metadataPath = p;
          break;
        }
      }

      if (!metadataPath) {
        logger.debug(
          'No versioning metadata file found in any of the paths. TypeScript source will not be available.',
        );
        logger.debug('Current directory:', process.cwd());
        logger.debug('__dirname:', __dirname);
        return;
      }

      logger.debug('Found metadata at:', metadataPath);

      // Load and parse metadata
      const content = fs.readFileSync(metadataPath, 'utf-8');
      this.metadata = JSON.parse(content) as VersioningMetadata;

      // Build lookup maps
      for (const [hash, func] of Object.entries(this.metadata.functions)) {
        this.functionsByHash.set(hash, func);
        this.functionsByName.set(func.name, func);
      }

      logger.info(
        `Loaded versioning metadata: ${Object.keys(this.metadata.functions).length} functions`,
      );
    } catch (error) {
      logger.debug('Failed to load metadata from file system:', error);
    }
  }

  /**
   * Load metadata from bundled data (for browser/webpack builds)
   */
  private loadFromBundle(): void {
    // In a browser environment, the metadata would need to be bundled
    // This is a placeholder - actual implementation would depend on the build system
    logger.debug('Browser environment detected. TypeScript metadata loading not implemented.');
  }

  /**
   * Get TypeScript source code by function hash
   */
  getByHash(hash: string): ExtractedFunction | null {
    this.load();
    return this.functionsByHash.get(hash) || null;
  }

  /**
   * Get TypeScript source code by function name
   */
  getByName(name: string): ExtractedFunction | null {
    this.load();
    return this.functionsByName.get(name) || null;
  }

  /**
   * Check if metadata is available
   */
  hasMetadata(): boolean {
    this.load();
    return this.metadata !== null;
  }

  /**
   * Get all extracted functions
   */
  getAllFunctions(): ExtractedFunction[] {
    this.load();
    return Array.from(this.functionsByHash.values());
  }
}

// Singleton instance
export const metadataLoader = new MetadataLoader();

/**
 * Helper function to get TypeScript source for a function
 */
export function getTypeScriptSource(hash: string, name?: string): string | null {
  // Try by hash first
  const byHash = metadataLoader.getByHash(hash);
  if (byHash) {
    // Prefer self-contained code if available
    return byHash.selfContainedCode || byHash.sourceCode;
  }

  // Fall back to name if provided
  if (name) {
    const byName = metadataLoader.getByName(name);
    if (byName) {
      // Prefer self-contained code if available
      return byName.selfContainedCode || byName.sourceCode;
    }
  }

  return null;
}
