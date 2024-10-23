import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { marked } from "marked";
import { SpanPublic } from "@/types/types";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import DOMPurify from "dompurify";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

interface ConversationItem {
  index: number;
  [key: string]: any;
}
interface GroupedItems {
  [key: string]: ConversationItem;
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
  index,
}: {
  item: any;
  sanitizedHtml: string;
  index: number;
}) => {
  return (
    <Card key={`${item.index}-${index}`}>
      <CardHeader>
        <CardTitle>{item.role}</CardTitle>
      </CardHeader>
      <CardContent
        className='flex flex-col overflow-auto'
        dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
      ></CardContent>
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
      const sanitizedHtml = convertStringtoHtml(item.content);
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
export const LlmPanel = ({ span }: { span: SpanPublic }) => {
  const data = span.data;
  const attributes = data.attributes;
  const groupedItems: GroupedItems = {};
  // Process each item in the data
  let messageIndex = 0;
  Object.entries(data.attributes).forEach(([key, value]) => {
    const parts = key.split(".");
    if (parts.length === 4) {
      const [itemType, itemCategory, index, field] = parts;
      const numericIndex = parseInt(index, 10);
      if (
        itemType === "gen_ai" &&
        (itemCategory === "completion" || itemCategory === "prompt")
      ) {
        if (!groupedItems[`${itemCategory}.${numericIndex}`]) {
          groupedItems[`${itemCategory}.${numericIndex}`] = {
            index: messageIndex,
          };
          messageIndex++;
        }
        groupedItems[`${itemCategory}.${numericIndex}`][field] = value;
      }
    }
  });
  const messages = convertItemsToCard(
    groupedItems,
    attributes["gen_ai.system"]
  );
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{data.name}</Typography>
      <div className='flex gap-1'>
        <Badge>{attributes["gen_ai.system"]}</Badge>
        <Badge>{attributes["gen_ai.response.model"]}</Badge>
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
