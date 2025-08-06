import OpenAI from 'openai';
import lilypad from '../src';

async function main() {
  lilypad.configure({ mode: 'debug' });

  const client = new OpenAI();
  lilypad.instrument_openai(client);

  const completion = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Hello!' }],
  });

  console.log('Completion:', completion.choices[0].message.content);
}

main().catch(console.error);
