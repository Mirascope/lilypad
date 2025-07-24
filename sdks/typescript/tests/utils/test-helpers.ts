import path from 'path';
import fs from 'fs';
import os from 'os';

export function createTempDir(prefix = 'lilypad-test-'): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

export function cleanupTempDir(dir: string): void {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

export function createTestMetadata(dir: string, fileName = 'lilypad-metadata.json'): void {
  const metadata = {
    version: '1.0.0',
    buildTime: new Date().toISOString(),
    functions: {
      hash123: {
        name: 'testFunction',
        hash: 'hash123',
        sourceCode: 'function testFunction() { return 42; }',
        selfContainedCode: '// Complete\nfunction testFunction() { return 42; }',
        signature: 'function testFunction()',
        filePath: 'src/test.ts',
        startLine: 1,
        endLine: 3,
        dependencies: {},
      },
      hash456: {
        name: 'anotherFunction',
        hash: 'hash456',
        sourceCode: 'const anotherFunction = () => "hello";',
        signature: 'const anotherFunction',
        filePath: 'src/another.ts',
        startLine: 5,
        endLine: 5,
        dependencies: {},
      },
    },
  };

  fs.writeFileSync(path.join(dir, fileName), JSON.stringify(metadata, null, 2));
}
