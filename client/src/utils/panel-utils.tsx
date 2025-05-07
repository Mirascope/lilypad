import { useAuth } from "@/auth";
import { CodeSnippet } from "@/components/CodeSnippet";
import { CollapsibleChevronTrigger } from "@/components/CollapsibleCard";
import { AddComment, CommentCards } from "@/components/Comment";
import { LilypadMarkdown } from "@/components/LilypadMarkdown";
import { TabGroup } from "@/components/TabGroup";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { AnnotationsTable } from "@/ee/components/AnnotationsTable";
import { CommentTab, Tab, TraceTab } from "@/types/traces";
import {
  Event,
  MessageParam,
  SpanMoreDetails,
  SpanPublic,
} from "@/types/types";
import { commentsBySpanQueryOptions } from "@/utils/comments";
import { safelyParseJSON, stringToBytes } from "@/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ReactNode } from "@tanstack/react-router";
import JsonView from "@uiw/react-json-view";
import { MessageSquareMore, NotebookPen } from "lucide-react";
import ReactMarkdown from "react-markdown";
export interface MessageCardProps {
  role: string;
  sanitizedHtml?: string;
  content?: ReactNode;
}
const MessageCard = ({ role, content }: MessageCardProps) => {
  return (
    <Card className="bg-primary-foreground">
      <CardHeader>
        <CardTitle>{role}</CardTitle>
      </CardHeader>
      <CardContent className="overflow-x-auto px-4">{content}</CardContent>
    </Card>
  );
};

export const renderMessagesCard = (
  messages: MessageParam[],
  renderer: "raw" | "markdown"
) => {
  try {
    return messages.map((message: MessageParam, index: number) => {
      const contents: ReactNode[] = [];
      let contentIndex = 0;
      for (const content of message.content) {
        const key = `messages-${index}-${contentIndex}`;
        if (content.type === "text") {
          if (renderer === "raw") {
            contents.push(
              <div key={key} className="whitespace-pre-line">
                {content.text}
              </div>
            );
          } else {
            contents.push(<LilypadMarkdown content={content.text} key={key} />);
          }
        } else if (content.type === "image") {
          const imgSrc = `data:${content.media_type};base64,${content.image}`;
          contents.push(<img key={key} src={imgSrc} alt="image" />);
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

export const SpanComments = ({ data }: { data: SpanPublic }) => {
  const { data: spanComments } = useSuspenseQuery(
    commentsBySpanQueryOptions(data.uuid)
  );
  const filteredAnnotations = data.annotations.filter(
    (annotation) => annotation.label
  );

  const tabs: Tab[] = [
    {
      label: (
        <>
          <MessageSquareMore /> Comments
          {spanComments.length > 0 && (
            <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {spanComments.length > 9 ? "9+" : spanComments.length}
            </div>
          )}
        </>
      ),
      value: CommentTab.COMMENTS,
      component: (
        <>
          <div className="overflow-y-auto mb-4">
            <CommentCards spanUuid={data.uuid} />
          </div>
          <Separator className="my-4" />
          <AddComment spanUuid={data.uuid} />
        </>
      ),
    },
    {
      label: (
        <>
          <NotebookPen /> Annotations
          {filteredAnnotations.length > 0 && (
            <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {filteredAnnotations.length > 9
                ? "9+"
                : filteredAnnotations.length}
            </div>
          )}
        </>
      ),
      value: CommentTab.ANNOTATIONS,
      component: <AnnotationsTable data={filteredAnnotations} />,
    },
  ];
  return (
    <Collapsible>
      <CollapsibleChevronTrigger />
      <CollapsibleContent>
        <TabGroup tabs={tabs} />
      </CollapsibleContent>
    </Collapsible>
  );
};
export const LilypadPanelTab = ({ span }: { span: SpanMoreDetails }) => {
  if (!span.code && !span.signature) return null;

  const tabs: Tab[] = [
    {
      label: "Output",
      value: TraceTab.OUTPUT,
      component: span.output ? (
        <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg shadow-sm overflow-auto">
          {renderOutput(span.output)}
        </div>
      ) : null,
    },
    {
      label: "Metadata",
      value: TraceTab.METADATA,
      component: span.data ? (
        <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg shadow-sm overflow-auto">
          {renderMetadata(span.data)}
        </div>
      ) : null,
    },
    {
      label: "Data",
      value: TraceTab.DATA,
      component: span.data && (
        <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg shadow-sm overflow-auto">
          <JsonView value={span.data} />
        </div>
      ),
    },
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

  return <TabGroup tabs={tabs} />;
};
export const renderEventsContainer = (messages: Event[]) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{"Events"}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {messages.map((event: Event, index: number) => (
          <Card key={`events-${index}`}>
            <CardHeader>
              <CardTitle>
                {event.name} {event.type && `[${event.type}]`}
              </CardTitle>
              <CardDescription>{event.timestamp}</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              {event.message}
            </CardContent>
          </Card>
        ))}
      </CardContent>
    </Card>
  );
};

export const MessagesContainer = ({
  messages,
}: {
  messages: MessageParam[];
}) => {
  const { updateUserConfig, userConfig } = useAuth();
  const defaultMessageRenderer =
    userConfig?.defaultMessageRenderer ?? "markdown";
  const handleChange = (checked: boolean) => {
    updateUserConfig({
      defaultMessageRenderer: checked ? "markdown" : "raw",
    });
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {"Messages"}
          <Switch
            checked={defaultMessageRenderer === "markdown"}
            onCheckedChange={handleChange}
          />
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {renderMessagesCard(messages, defaultMessageRenderer)}
      </CardContent>
    </Card>
  );
};
export const renderOutput = (output: string) => {
  const jsonOutput = safelyParseJSON(output);
  return (
    <>
      {typeof jsonOutput === "object" ? (
        <JsonView shortenTextAfterLength={100} value={jsonOutput} />
      ) : (
        <ReactMarkdown>{output}</ReactMarkdown>
      )}
    </>
  );
};

export const renderMetadata = (data: Record<string, any>) => {
  const attributes = data.attributes;
  if (!attributes || typeof attributes !== "object") return null;
  if ("type" in attributes && attributes.type !== "traces") return null;
  return <JsonView value={attributes} />;
};
