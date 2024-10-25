import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { marked } from "marked";
import { SpanPublic } from "@/types/types";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import DOMPurify from "dompurify";
import { ReactNode } from "react";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

interface ConversationItem {
  index: number;
  [key: string]: any;
}

const convertStringtoHtml = (content: string): string => {
  const rawHtml: string = marked.parse(content, {
    async: false,
  });
  return DOMPurify.sanitize(rawHtml);
};

const renderMessageCard = ({
  item,
  sanitizedHtml,
  content,
  index,
}: {
  item: any;
  sanitizedHtml?: string;
  content?: ReactNode;
  index: number;
}) => {
  let cardContent = null;
  if (sanitizedHtml) {
    cardContent = (
      <CardContent
        className='flex flex-col overflow-auto'
        dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
      />
    );
  } else if (content) {
    cardContent = (
      <CardContent className='flex flex-col'>{content}</CardContent>
    );
  }
  return (
    <Card key={`${item.index}-${index}`}>
      <CardHeader>
        <CardTitle>{item.role}</CardTitle>
      </CardHeader>
      {cardContent}
    </Card>
  );
};
const convertItemsToOpenAICard = (items: ConversationItem) => {
  const cards = [];
  const messages = Object.values(items);
  messages.forEach((item) => {
    try {
      const parsedContent = JSON.parse(item.content);
      if (Array.isArray(parsedContent)) {
        parsedContent.forEach((content, index) => {
          if (content.type === "text") {
            const sanitizedHtml = convertStringtoHtml(content.text);
            cards.push(
              renderMessageCard({
                item,
                sanitizedHtml,
                index,
              })
            );
          } else if (content.type === "image_url") {
            cards.push(
              renderMessageCard({
                item,
                sanitizedHtml: `<img src="${content.image_url.url}" alt="image" />`,
                index,
              })
            );
          }
        });
      } else {
        const sanitizedHtml = convertStringtoHtml(item.content);
        cards.push(
          renderMessageCard({
            item,
            sanitizedHtml,
          })
        );
      }
    } catch (e) {
      if (item.finish_reason === "tool_calls") {
        item.role = "assistant";
        const toolCalls = item.tool_calls;
        const content = toolCalls.map((toolCall) => {
          return (
            <div key={toolCall.id}>
              <h4>{toolCall.name}</h4>
              <pre className='overflow-auto'>
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
          );
        });
        cards.push(
          renderMessageCard({
            item,
            content,
          })
        );
      } else {
        const sanitizedHtml = convertStringtoHtml(item.content);
        cards.push(
          renderMessageCard({
            item,
            sanitizedHtml,
          })
        );
      }
    }
  });
  return cards;
};

const convertItemsToGeminiCard = (items: ConversationItem) => {
  const cards = [];
  const messages = Object.values(items);
  for (const item of messages) {
    if (!item.content && !item.user) continue;
    if (item.user) item.role = "user";
    else if (item.content) item.role = "assistant";

    let content = item.user || item.content;
    const sanitizedHtml = convertStringtoHtml(content);
    cards.push(
      renderMessageCard({
        item,
        sanitizedHtml,
      })
    );
  }
  return cards;
};
const convertItemsToAnthropicCard = (items: ConversationItem) => {
  const cards = [];
  const messages = Object.values(items);
  messages.forEach((item) => {
    try {
      const parsedContent = JSON.parse(item.content);
      if (Array.isArray(parsedContent)) {
        parsedContent.forEach((content, index) => {
          if (content.type === "text") {
            const sanitizedHtml = convertStringtoHtml(content.text);
            cards.push(
              renderMessageCard({
                item,
                sanitizedHtml,
                index,
              })
            );
          } else if (content.type === "image_url") {
            cards.push(
              renderMessageCard({
                item,
                sanitizedHtml: `<img src="${content.image_url.url}" alt="image" />`,
                index,
              })
            );
          }
        });
      } else {
        const sanitizedHtml = convertStringtoHtml(item.content);
        if (item.finish_reason) {
          item.role = "assistant";
        }
        cards.push(
          renderMessageCard({
            item,
            sanitizedHtml,
          })
        );
      }
    } catch (e) {
      const sanitizedHtml = convertStringtoHtml(item.content);
      if (item.finish_reason) {
        item.role = "assistant";
      }
      cards.push(
        renderMessageCard({
          item,
          sanitizedHtml,
        })
      );
    }
  });
  return cards;
};
const convertItemsToCard = (items: ConversationItem, provider: string) => {
  if (provider === "OpenAI") {
    return convertItemsToOpenAICard(items);
  } else if (provider === "Gemini") {
    return convertItemsToGeminiCard(items);
  } else if (provider === "Anthropic") {
    return convertItemsToAnthropicCard(items);
  }
};
const groupKeys = (attributes) => {
  const groupedItems = {};
  let messageIndex = 0;

  Object.entries(attributes).forEach(([key, value]) => {
    // Only process gen_ai related keys
    if (!key.startsWith("gen_ai.")) return;

    // Remove the "gen_ai" prefix for easier processing
    const keyWithoutPrefix = key.substring("gen_ai.".length);
    const keyParts = keyWithoutPrefix.split(".");

    // Get the base category (prompt or completion) and its index
    const itemCategory = keyParts[0];
    const itemIndex = keyParts[1];

    if (itemCategory !== "prompt" && itemCategory !== "completion") return;

    // Create the group key
    const groupKey = `${itemCategory}.${itemIndex}`;

    // Initialize group if it doesn't exist
    if (!groupedItems[groupKey]) {
      groupedItems[groupKey] = {
        index: messageIndex++,
      };
    }

    // Handle tool_calls specially
    if (keyParts[2] === "tool_calls") {
      const toolCallIndex = keyParts[3];
      const toolCallField = keyParts[4];

      // Initialize tool_calls array if it doesn't exist
      if (!groupedItems[groupKey].tool_calls) {
        groupedItems[groupKey].tool_calls = [];
      }

      // Initialize specific tool call object if it doesn't exist
      if (!groupedItems[groupKey].tool_calls[toolCallIndex]) {
        groupedItems[groupKey].tool_calls[toolCallIndex] = {};
      }

      // Parse JSON arguments if present
      if (toolCallField === "arguments" && typeof value === "string") {
        try {
          groupedItems[groupKey].tool_calls[toolCallIndex][toolCallField] =
            JSON.parse(value);
        } catch (e) {
          groupedItems[groupKey].tool_calls[toolCallIndex][toolCallField] =
            value;
        }
      } else {
        groupedItems[groupKey].tool_calls[toolCallIndex][toolCallField] = value;
      }
    } else {
      // Handle regular fields
      groupedItems[groupKey][keyParts[2]] = value;
    }
  });

  return groupedItems;
};
export const LlmPanel = ({ span }: { span: SpanPublic }) => {
  const data = span.data;
  const attributes = data.attributes;
  const messages = convertItemsToCard(
    groupKeys(attributes),
    attributes["gen_ai.system"]
  );
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{data.name}</Typography>
      <div className='flex gap-1'>
        <Badge>{attributes["gen_ai.system"]}</Badge>
        <Badge>{attributes["gen_ai.response.model"]}</Badge>
        {attributes["gen_ai.usage.prompt_tokens"] &&
          attributes["gen_ai.usage.completion_tokens"] && (
            <Badge className='text-xs font-medium m-0'>
              <span>{attributes["gen_ai.usage.prompt_tokens"]}</span>
              <span className='mx-1'>&#8594;</span>
              <span>{attributes["gen_ai.usage.completion_tokens"]}</span>
              <span className='mx-1'>=</span>
              <span>
                {attributes["gen_ai.usage.prompt_tokens"] +
                  attributes["gen_ai.usage.completion_tokens"]}
              </span>
            </Badge>
          )}
        <Badge>
          {((data.end_time - data.start_time) / 1_000_000_000).toFixed(3)}s
        </Badge>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{"Messages"}</CardTitle>
        </CardHeader>
        <CardContent className='flex flex-col gap-4'>{messages}</CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{"Data"}</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className='overflow-auto'>{JSON.stringify(data, null, 2)}</pre>
        </CardContent>
      </Card>
    </div>
  );
};
