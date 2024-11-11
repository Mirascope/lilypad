import { GeminiCallArgsCreate } from "@/types/types";

export const geminiCallParamsForm = () => {
  const geminiCallParamsDefault: GeminiCallArgsCreate = {
    response_mime_type: "text/plain",
    max_output_tokens: undefined,
    temperature: undefined,
    top_p: undefined,
    top_k: undefined,
    frequency_penalty: undefined,
    presence_penalty: undefined,
    response_schema: undefined,
  };
};
