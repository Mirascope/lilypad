import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { SpanPublic } from "@/types/types";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import { ReactElement, ReactNode } from "react";
import { MessageCard, MessageCardProps } from "@/components/MessageCard";
import ReactMarkdown from "react-markdown";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

interface ConversationItem {
  index: number;
  [key: string]: any;
}

const convertItemsToOpenAICard = (items: ConversationItem) => {
  const cards: ReactElement<MessageCardProps>[] = [];
  const messages = Object.values(items);
  messages.forEach((item, mIndex) => {
    try {
      const parsedContent = JSON.parse(item.content);
      if (Array.isArray(parsedContent)) {
        const cardContent: ReactNode[] = [];
        parsedContent.forEach((content, index) => {
          const key = `messages-${mIndex}-${index}`;
          if (content.type === "text") {
            cardContent.push(
              <ReactMarkdown key={key}>{content.text}</ReactMarkdown>
            );
          } else if (content.type === "image_url") {
            cardContent.push(
              <img key={key} src={`${content.image_url.url}`} alt='image' />
            );
          }
        });
        cards.push(
          <MessageCard role={item.role} content={cardContent} key={mIndex} />
        );
      } else {
        cards.push(
          <MessageCard
            role={item.role}
            content={<ReactMarkdown>{item.content}</ReactMarkdown>}
            key={mIndex}
          />
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
          <MessageCard role={item.role} content={content} key={mIndex} />
        );
      } else {
        cards.push(
          <MessageCard
            role={item.role}
            content={<ReactMarkdown>{item.content}</ReactMarkdown>}
            key={mIndex}
          />
        );
      }
    }
  });
  return cards;
};

const convertItemsToGeminiCard = (items: ConversationItem) => {
  const cards: ReactElement<MessageCardProps>[] = [];
  const messages = Object.values(items);
  let index = 0;
  for (const item of messages) {
    if (!item.content && !item.user) continue;
    if (item.user) item.role = "user";
    else if (item.content) item.role = "assistant";

    let content = item.user || item.content;
    cards.push(
      <MessageCard
        role={item.role}
        content={<ReactMarkdown>{content}</ReactMarkdown>}
        key={index}
      />
    );
    index++;
  }
  return cards;
};
const convertItemsToAnthropicCard = (items: ConversationItem) => {
  const cards: ReactElement<MessageCardProps>[] = [];
  const messages = Object.values(items);
  messages.forEach((item, mIndex) => {
    try {
      const parsedContent = JSON.parse(item.content);
      if (Array.isArray(parsedContent)) {
        const cardContent: ReactNode[] = [];
        parsedContent.forEach((content, index) => {
          if (content.type === "text") {
            cardContent.push(
              <ReactMarkdown key={`${mIndex}-${index}`}>
                {content.text}
              </ReactMarkdown>
            );
          } else if (content.type === "image_url") {
            cardContent.push(
              <img
                key={`${mIndex}-${index}`}
                src='${content.image_url.url}'
                alt='image'
              />
            );
          }
        });
        cards.push(
          <MessageCard role={item.role} content={cardContent} key={mIndex} />
        );
      } else {
        if (item.finish_reason) {
          item.role = "assistant";
        }
        cards.push(
          <MessageCard
            role={item.role}
            content={<ReactMarkdown>{item.content}</ReactMarkdown>}
            key={mIndex}
          />
        );
      }
    } catch (e) {
      if (item.finish_reason) {
        item.role = "assistant";
      }
      cards.push(
        <MessageCard
          role={item.role}
          content={<ReactMarkdown>{item.content}</ReactMarkdown>}
          key={mIndex}
        />
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
