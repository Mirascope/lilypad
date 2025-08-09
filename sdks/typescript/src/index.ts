import type { LilypadConfig } from './configure';
import { configure } from './configure';
import { instrument_openai } from './opentelemetry/instrument-openai';

const lilypad = {
  configure,
  instrument_openai,
};

export default lilypad;
export { configure, instrument_openai };
export type { LilypadConfig };
