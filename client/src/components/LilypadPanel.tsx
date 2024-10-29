import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { SpanPublic } from "@/types/types";
import { CodeSnippet } from "@/routes/-codeSnippet";
import { Typography } from "@/components/ui/typography";
import { ArgsCards } from "@/components/ArgsCards";
import { stringToBytes } from "@/utils/strings";
import { MessageCard } from "@/components/MessageCard";
import { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

const renderLilypadMessageCard = (serializedMessages: string) => {
  try {
    const messages = JSON.parse(serializedMessages);
    return messages.map((message: any, index: number) => {
      const contents: ReactNode[] = [];
      let contentIndex = 0;
      if (message.content) {
        for (const content of message.content) {
          const key = `messages-${index}-${contentIndex}`;
          if (content.type === "text") {
            contents.push(
              <ReactMarkdown key={key}>{content.text}</ReactMarkdown>
            );
          } else if (content.type === "image_url") {
            contents.push(
              <img key={key} src={`${content.image_url.url}`} alt='image' />
            );
          }
          contentIndex++;
        }
      } else if (message.parts) {
        for (const part of message.parts) {
          const key = `messages-${index}-${contentIndex}`;
          if (typeof part === "string") {
            contents.push(<ReactMarkdown key={key}>{part}</ReactMarkdown>);
          } else if (part.mime_type.startsWith("audio")) {
            const data = stringToBytes(part.data);
            const blob = new Blob([data], { type: part.mime_type });
            const url = URL.createObjectURL(blob);
            contents.push(<audio key={key} src={url} controls />);
          }
          contentIndex++;
        }
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
export const LilypadPanel = ({ span }: { span: SpanPublic }) => {
  const data = span.data;
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{data.name}</Typography>
      <Card>
        <CardHeader>
          <CardTitle>{"Code"}</CardTitle>
        </CardHeader>
        <CardContent>
          <CodeSnippet code={data.attributes["lilypad.lexical_closure"]} />
        </CardContent>
      </Card>
      <ArgsCards args={JSON.parse(data.attributes["lilypad.arg_values"])} />
      {data.attributes["lilypad.prompt_template"] && (
        <Card>
          <CardHeader>
            <CardTitle>{"Prompt Template"}</CardTitle>
          </CardHeader>
          <CardContent className='whitespace-pre-wrap'>
            {data.attributes["lilypad.prompt_template"]}
          </CardContent>
        </Card>
      )}
      {data.attributes["lilypad.messages"] && (
        <Card>
          <CardHeader>
            <CardTitle>{"Messages"}</CardTitle>
          </CardHeader>
          <CardContent className='flex flex-col gap-4'>
            {renderLilypadMessageCard(data.attributes["lilypad.messages"])}
          </CardContent>
        </Card>
      )}
      {data.attributes["lilypad.output"] && (
        <Card>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex flex-col'>
            <ReactMarkdown>{data.attributes["lilypad.output"]}</ReactMarkdown>
          </CardContent>
        </Card>
      )}
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
