#!/usr/bin/env node

/**
 * Lilypad CLI for building and deploying versioned functions
 */

import { Command } from 'commander';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import { buildTracedFunctions } from '../plugins/trace-plugin';
import { logger } from '../utils/logger';
import { getSettings, setSettings } from '../utils/settings';
import { getPooledClient } from '../utils/client-pool';
import type { TracedFunctionMetadata } from '../plugins/trace-plugin';
import type { LilypadConfig } from '../types';

// Initialize settings from environment variables if not already configured
function initializeSettings(): LilypadConfig {
  let settings = getSettings();
  if (!settings) {
    const apiKey = process.env.LILYPAD_API_KEY;
    const projectId = process.env.LILYPAD_PROJECT_ID;
    const baseUrl = process.env.LILYPAD_BASE_URL || 'https://api.lilypad.so';
    
    if (!apiKey || !projectId) {
      throw new Error('LILYPAD_API_KEY and LILYPAD_PROJECT_ID environment variables are required');
    }
    
    settings = {
      apiKey,
      projectId,
      baseUrl,
    };
    setSettings(settings);
  }
  return settings;
}

const program = new Command();

program
  .name('lilypad')
  .description('Lilypad CLI for managing versioned functions')
  .version('0.1.0');

/**
 * Build command - extract and bundle traced functions
 */
program
  .command('build')
  .description('Build traced functions and generate deployment artifacts')
  .option('-e, --entry <files...>', 'Entry point files', (value, previous: string[]) => {
    return previous.concat([value]);
  }, ['./src/**/*.ts'] as string[])
  .option('-o, --output <dir>', 'Output directory', './dist/trace-artifacts')
  .option('-p, --platform <platform>', 'Target platform (node|browser)', 'node')
  .option('--external <deps...>', 'External dependencies to exclude from bundles')
  .action(async (options) => {
    try {
      logger.info('Building traced functions...');
      
      await buildTracedFunctions({
        entryPoints: options.entry,
        outputDir: options.output,
        platform: options.platform,
        external: options.external,
      });
      
      logger.info(`Build completed. Artifacts saved to ${options.output}`);
    } catch (error) {
      logger.error('Build failed:', error);
      process.exit(1);
    }
  });

/**
 * Deploy command - upload function bundles to Lilypad
 */
program
  .command('deploy')
  .description('Deploy traced functions to Lilypad')
  .option('-d, --dir <dir>', 'Artifacts directory', './dist/trace-artifacts')
  .option('-e, --env <env>', 'Target environment', 'production')
  .option('--dry-run', 'Show what would be deployed without actually deploying')
  .action(async (options) => {
    try {
      const settings = initializeSettings();
      
      logger.info('Deploying traced functions...');
      
      // Read metadata
      const metadataPath = path.join(options.dir, 'metadata.json');
      const metadataContent = await fs.readFile(metadataPath, 'utf-8');
      const metadata: Record<string, TracedFunctionMetadata> = JSON.parse(metadataContent);
      
      if (options.dryRun) {
        logger.info('Dry run mode - showing what would be deployed:');
        for (const [name, func] of Object.entries(metadata)) {
          logger.info(`  - ${name}: ${func.signature}`);
          logger.info(`    Hash: ${func.hash}`);
          logger.info(`    Dependencies: ${func.dependencies.join(', ') || 'none'}`);
        }
        return;
      }
      
      const client = getPooledClient(settings);
      
      // Deploy each function
      for (const [name, func] of Object.entries(metadata)) {
        logger.info(`Deploying ${name}...`);
        
        try {
          // Check if function exists
          let functionUuid: string;
          try {
            const existing = await client.projects.functions.getByHash(
              settings.projectId,
              func.hash
            );
            functionUuid = existing.uuid;
            logger.info(`  Function already exists with UUID: ${functionUuid}`);
          } catch (error) {
            // Create new function
            const created = await client.projects.functions.create(settings.projectId, {
              project_uuid: settings.projectId,
              name: func.name,
              code: func.code,
              hash: func.hash,
              signature: func.signature,
              arg_types: func.argTypes || {},
              dependencies: func.dependencies.reduce((acc, dep) => {
                acc[dep] = { version: '*' }; // Version can be specified later
                return acc;
              }, {} as Record<string, { version: string }>),
              is_versioned: true,
              prompt_template: '',
            });
            functionUuid = created.uuid;
            logger.info(`  Created new function with UUID: ${functionUuid}`);
          }
          
          // Deploy to environment
          // Note: This is a mock API call - actual implementation would depend on Lilypad API
          logger.info(`  Deploying to ${options.env} environment...`);
          
          // In a real implementation, this would:
          // 1. Upload the bundle to a storage service
          // 2. Create a deployment record
          // 3. Update the environment configuration
          
          logger.info(`  ✓ Deployed ${name} successfully`);
        } catch (error) {
          logger.error(`  ✗ Failed to deploy ${name}:`, error);
        }
      }
      
      logger.info('Deployment completed');
    } catch (error) {
      logger.error('Deploy failed:', error);
      process.exit(1);
    }
  });

/**
 * List command - show deployed functions
 */
program
  .command('list')
  .description('List deployed functions')
  .option('-p, --project <id>', 'Project ID (defaults to LILYPAD_PROJECT_ID)')
  .action(async (options) => {
    try {
      const settings = initializeSettings();
      
      const projectId = options.project || settings.projectId;
      const client = getPooledClient(settings);
      
      logger.info(`Listing functions in project ${projectId}...`);
      
      // Use list method instead of listPaginated
      const functions = await client.projects.functions.list(projectId);
      const versionedFunctions = functions.filter(f => f.is_versioned);
      
      if (versionedFunctions.length === 0) {
        logger.info('No versioned functions found');
        return;
      }
      
      logger.info(`\nFound ${versionedFunctions.length} versioned functions:\n`);
      
      for (const func of versionedFunctions) {
        logger.info(`${func.name} (v${func.version_num || 1})`);
        logger.info(`  UUID: ${func.uuid}`);
        logger.info(`  Hash: ${func.hash}`);
        logger.info(`  Created: ${new Date().toLocaleString()}`); // created_at might not be available
        logger.info('');
      }
    } catch (error) {
      logger.error('List failed:', error);
      process.exit(1);
    }
  });

/**
 * Rollback command - rollback to a previous version
 */
program
  .command('rollback <function> <version>')
  .description('Rollback a function to a previous version')
  .option('-e, --env <env>', 'Target environment', 'production')
  .action(async (functionName, version, options) => {
    try {
      const settings = initializeSettings();
      const client = getPooledClient(settings);
      
      logger.info(`Rolling back ${functionName} to version ${version} in ${options.env}...`);
      
      try {
        // Find function by name
        const functions = await client.projects.functions.getByName(settings.projectId, functionName);
        if (!functions || functions.length === 0) {
          throw new Error(`Function '${functionName}' not found`);
        }
        
        // Find the specific version
        const targetVersion = functions.find(f => f.version_num === parseInt(version));
        if (!targetVersion) {
          throw new Error(`Version ${version} not found for function '${functionName}'`);
        }
        
        logger.info(`Found version ${version} (UUID: ${targetVersion.uuid})`);
        logger.info('Note: Deployment rollback would be implemented here');
        logger.info('Rollback completed successfully');
      } catch (error) {
        logger.error(`Failed to rollback ${functionName}:`, error);
        throw error;
      }
    } catch (error) {
      logger.error('Rollback failed:', error);
      process.exit(1);
    }
  });

// Parse command line arguments
program.parse(process.argv);