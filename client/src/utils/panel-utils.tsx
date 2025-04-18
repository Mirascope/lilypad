import { useAuth } from "@/auth";
import { CodeSnippet } from "@/components/CodeSnippet";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tab, TraceTab } from "@/types/traces";
import { Event, MessageParam, SpanMoreDetails } from "@/types/types";
import { safelyParseJSON, stringToBytes } from "@/utils/strings";
import { ReactNode } from "@tanstack/react-router";
import JsonView, { JsonViewProps } from "@uiw/react-json-view";
import ReactMarkdown from "react-markdown";
export interface MessageCardProps {
  role: string;
  sanitizedHtml?: string;
  content?: ReactNode;
}
const MessageCard = ({ role, content }: MessageCardProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{role}</CardTitle>
      </CardHeader>
      <CardContent className='overflow-x-auto'>{content}</CardContent>
    </Card>
  );
};

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

export const TraceCodeTab = ({ span }: { span: SpanMoreDetails }) => {
  const { userConfig, updateUserConfig } = useAuth();
  if (!span.code && !span.signature) return null;
  const tabs: Tab[] = [
    {
      label: "Code",
      value: TraceTab.CODE,
      component: <CodeSnippet code={span.code ?? ""} />,
    },
    {
      label: "Signature",
      value: TraceTab.SIGNATURE,
      component: <CodeSnippet code={span.signature ?? ""} />,
    },
  ];
  return (
    <Tabs
      defaultValue={userConfig?.defaultTraceTab ?? "signature"}
      className='w-full'
    >
      <div className='flex w-full'>
        <TabsList className={`w-[160px]`}>
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              onClick={() =>
                updateUserConfig({
                  defaultTraceTab: tab.value,
                })
              }
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      {tabs.map((tab) => (
        <TabsContent
          key={tab.value}
          value={tab.value}
          className='w-full bg-gray-50'
        >
          {tab.component}
        </TabsContent>
      ))}
    </Tabs>
  );
};

export const renderEventsContainer = (messages: Event[]) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{"Events"}</CardTitle>
      </CardHeader>
      <CardContent className='flex flex-col gap-4'>
        {messages.map((event: Event, index: number) => (
          <Card key={`events-${index}`}>
            <CardHeader>
              <CardTitle>
                {event.name} {event.type && `[${event.type}]`}
              </CardTitle>
              <CardDescription>{event.timestamp}</CardDescription>
            </CardHeader>
            <CardContent className='overflow-x-auto'>
              {event.message}
            </CardContent>
          </Card>
        ))}
      </CardContent>
    </Card>
  );
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
          <CardContent className='flex flex-col overflow-x-auto'>
            {renderOutput(output)}
          </CardContent>
        </Card>
      )}
    </>
  );
};

export const renderMetadata = (data: Record<string, any>) => {
  const attributes = data.attributes;
  if (!attributes) return null;
  if (attributes.type && attributes.type !== "traces") return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>{"Metadata"}</CardTitle>
      </CardHeader>
      {attributes && (
        <CardContent className='overflow-x-auto'>
          <JsonView value={attributes} />
        </CardContent>
      )}
    </Card>
  );
};
export const renderData = ({ ...props }: JsonViewProps<object>) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{"Data"}</CardTitle>
      </CardHeader>
      {props.value && (
        <CardContent className='overflow-x-auto'>
          <JsonView value={props.value} collapsed={props.collapsed} />
        </CardContent>
      )}
    </Card>
  );
};
