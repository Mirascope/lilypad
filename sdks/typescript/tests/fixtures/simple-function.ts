import { trace } from '@lilypad/typescript-sdk';

const greeting = 'Hello';

function formatName(name: string): string {
  return name.toUpperCase();
}

export const greetUser = trace(
  (name: string) => {
    return `${greeting}, ${formatName(name)}!`;
  },
  { versioning: 'automatic', name: 'greetUser' },
);
