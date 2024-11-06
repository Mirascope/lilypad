import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { MessageParam, SpanMoreDetails } from "@/types/types";
import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import { MessageCard } from "@/components/MessageCard";
import ReactMarkdown from "react-markdown";
import { useQuery } from "@tanstack/react-query";
import api from "@/api";
import { AxiosResponse } from "axios";
import { ReactNode } from "@tanstack/react-router";
import { stringToBytes } from "@/utils/strings";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

const renderMessagesCard = (messages: MessageParam[]) => {
  try {
    return messages.map((message: MessageParam, index: number) => {
      const contents: ReactNode[] = [];
      let contentIndex = 0;
      for (const content of message.content) {
        const key = `messages-${index}-${contentIndex}`;
        if (content.type === "text") {
          contents.push(
            <ReactMarkdown key={key}>{content.text}</ReactMarkdown>
          );
        } else if (content.type === "image") {
          const imgSrc = `data:${content.media_type};base64,${content.image}`;
          contents.push(<img key={key} src={imgSrc} alt='image' />);
        } else if (content.type === "audio") {
          const data = stringToBytes(content.audio);
          const blob = new Blob([data], { type: content.media_type });
          const url = URL.createObjectURL(blob);
          contents.push(<audio key={key} src={url} controls />);
        } else if (content.type === "tool_call") {
          contents.push(
            <Card key={key}>
              <CardHeader>
                <CardTitle>{content.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className='overflow-auto'>
                  {JSON.stringify(content.arguments, null, 2)}
                </pre>
              </CardContent>
            </Card>
          );
        }
        contentIndex++;
      }
      return (
        <MessageCard
          role={message.role}
          content={contents}
          key={`messages-${index}`}
        />
      );
    });
  } catch (e) {
    return null;
  }
};

export const LlmPanel = ({ spanId }: { spanId: string }) => {
  const {
    data: span,
    isLoading,
    error,
  } = useQuery<SpanMoreDetails>({
    queryKey: ["span", spanId],
    queryFn: async () =>
      (await api.get<null, AxiosResponse<SpanMoreDetails>>(`spans/${spanId}`))
        .data,
  });
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>{error.message}</div>;
  if (!span) return <div>Span not found</div>;

  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{span.display_name}</Typography>
      <div className='flex gap-1'>
        <Badge>{span.provider}</Badge>
        <Badge>{span.model}</Badge>
        {span.prompt_tokens && span.completion_tokens && (
          <Badge className='text-xs font-medium m-0'>
            <span>{span.prompt_tokens}</span>
            <span className='mx-1'>&#8594;</span>
            <span>{span.completion_tokens}</span>
            <span className='mx-1'>=</span>
            <span>{span.prompt_tokens + span.completion_tokens}</span>
          </Badge>
        )}
        <Badge>{(span.duration_ms / 1_000_000_000).toFixed(3)}s</Badge>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{"Messages"}</CardTitle>
        </CardHeader>
        <CardContent className='flex flex-col gap-4'>
          {renderMessagesCard(span.messages)}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{"Data"}</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className='overflow-auto'>
            {JSON.stringify(span.data, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
};
