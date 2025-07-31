import { describe, expect, it } from 'vitest';
import * as dbExports from './index';
import * as middlewareExports from './middleware';
import * as schemaExports from './schema';

describe('db/index.ts exports', () => {
  it('should re-export all middleware exports', () => {
    // Check that all middleware exports are available through the index
    expect(dbExports.dbMiddleware).toBeDefined();
    expect(dbExports.dbMiddleware).toBe(middlewareExports.dbMiddleware);
  });

  it('should re-export all schema exports', () => {
    // Check that all schema exports are available through the index
    expect(dbExports.users).toBeDefined();
    expect(dbExports.users).toBe(schemaExports.users);

    expect(dbExports.sessions).toBeDefined();
    expect(dbExports.sessions).toBe(schemaExports.sessions);

    expect(dbExports.organizations).toBeDefined();
    expect(dbExports.organizations).toBe(schemaExports.organizations);

    expect(dbExports.organizationMemberships).toBeDefined();
    expect(dbExports.organizationMemberships).toBe(
      schemaExports.organizationMemberships
    );

    expect(dbExports.userConsents).toBeDefined();
    expect(dbExports.userConsents).toBe(schemaExports.userConsents);
  });

  it('should export the same objects as the source modules', () => {
    // Verify that the exports are the exact same references
    const middlewareKeys = Object.keys(middlewareExports) as Array<
      keyof typeof middlewareExports
    >;
    const schemaKeys = Object.keys(schemaExports) as Array<
      keyof typeof schemaExports
    >;

    // Check that all middleware exports are present
    middlewareKeys.forEach((key) => {
      expect(dbExports[key as keyof typeof dbExports]).toBeDefined();
      expect(dbExports[key as keyof typeof dbExports]).toBe(
        middlewareExports[key]
      );
    });

    // Check that all schema exports are present
    schemaKeys.forEach((key) => {
      expect(dbExports[key as keyof typeof dbExports]).toBeDefined();
      expect(dbExports[key as keyof typeof dbExports]).toBe(schemaExports[key]);
    });
  });

  it('should have all expected exports', () => {
    // List of expected exports from both modules
    const expectedExports = [
      // From middleware
      'dbMiddleware',
      // From schema
      'users',
      'sessions',
      'organizations',
      'organizationMemberships',
      'userConsents',
    ];

    expectedExports.forEach((exportName) => {
      expect(dbExports[exportName as keyof typeof dbExports]).toBeDefined();
    });
  });
});
