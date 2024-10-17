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
  const messages = Object.values(groupedItems).map((item) => {
    const rawHtml: string = marked.parse(item.content, {
      async: false,
    });
    const sanitizedHtml = DOMPurify.sanitize(rawHtml);
    return (
      <Card key={item.index}>
        <CardHeader>
          <CardTitle>{item.role}</CardTitle>
        </CardHeader>
        <CardContent
          className='flex flex-col'
          dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
        ></CardContent>
      </Card>
    );
  });
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
