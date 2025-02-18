import { MessageCard } from "@/components/MessageCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageParam } from "@/types/types";
import { safelyParseJSON, stringToBytes } from "@/utils/strings";
import { ReactNode } from "@tanstack/react-router";
import JsonView, { JsonViewProps } from "@uiw/react-json-view";
import ReactMarkdown from "react-markdown";

export const renderMessagesCard = (messages: MessageParam[]) => {
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
                <JsonView value={content.arguments} />
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

export const renderMessagesContainer = (messages: MessageParam[]) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{"Messages"}</CardTitle>
      </CardHeader>
      <CardContent className='flex flex-col gap-4'>
        {renderMessagesCard(messages)}
      </CardContent>
    </Card>
  );
};
export const renderOutput = (output: any) => {
  const jsonOutput = safelyParseJSON(output);
  return (
    <>
      {jsonOutput ? (
        <JsonView value={jsonOutput} />
      ) : (
        <ReactMarkdown>{output}</ReactMarkdown>
      )}
    </>
  );
};
export const renderCardOutput = (output: any) => {
  return (
    <>
      {output && (
        <Card>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex flex-col'>
            {renderOutput(output)}
          </CardContent>
        </Card>
      )}
    </>
  );
};

export const renderData = ({ ...props }: JsonViewProps<object>) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{"Data"}</CardTitle>
      </CardHeader>
      {props.value && (
        <CardContent>
          <JsonView value={props.value} collapsed={props.collapsed} />
        </CardContent>
      )}
    </Card>
  );
};
