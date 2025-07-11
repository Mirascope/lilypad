import { useAuth } from "@/src/auth";
import { CodeBlock } from "@/src/components/code-block";
import { AddComment, CommentCards } from "@/src/components/Comment";
import { JsonView } from "@/src/components/JsonView";
import { LilypadMarkdown } from "@/src/components/LilypadMarkdown";
import { TabGroup } from "@/src/components/TabGroup";
import { Button } from "@/src/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/src/components/ui/card";
import { Separator } from "@/src/components/ui/separator";
import { AnnotationsTable } from "@/src/ee/components/AnnotationsTable";
import { annotationsBySpanQueryOptions } from "@/src/ee/utils/annotations";
import { useFeatureAccess } from "@/src/hooks/use-featureaccess";
import { CommentTab, Tab, TraceTab } from "@/src/types/traces";
import { AnnotationPublic, Event, MessageParam, SpanMoreDetails } from "@/src/types/types";
import { commentsBySpanQueryOptions } from "@/src/utils/comments";
import { safelyParseJSON, stringToBytes } from "@/src/utils/strings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { MessageSquareMore, NotebookPen } from "lucide-react";
import { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
export interface MessageCardProps {
  role: string;
  sanitizedHtml?: string;
  content?: ReactNode;
}
const MessageCard = ({ role, content }: MessageCardProps) => {
  return (
    <Card className="bg-background">
      <CardHeader className="px-4">
        <CardTitle>{role}</CardTitle>
      </CardHeader>
      <CardContent className="professional overflow-x-auto px-4">{content}</CardContent>
    </Card>
  );
};

export const renderMessagesCard = (messages: MessageParam[], renderer: "raw" | "markdown") => {
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
      return <MessageCard role={message.role} content={contents} key={`messages-${index}`} />;
    });
  } catch (e) {
    return null;
  }
};

export const SpanComments = ({
  projectUuid,
  spanUuid,
  activeAnnotation,
}: {
  projectUuid: string;
  spanUuid: string;
  activeAnnotation?: AnnotationPublic | null;
}) => {
  const features = useFeatureAccess();
  const { data: spanComments } = useSuspenseQuery(commentsBySpanQueryOptions(spanUuid));
  const { data: annotations } = useSuspenseQuery(
    annotationsBySpanQueryOptions(projectUuid, spanUuid, features.annotations)
  );
  const filteredAnnotations = annotations.filter((annotation) => annotation.label);

  const tabs: Tab[] = [
    {
      label: (
        <div className="flex items-center gap-1">
          <MessageSquareMore />
          <span>Discussion</span>
          {spanComments.length > 0 && (
            <div className="absolute -top-0 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-secondary text-xs font-medium text-primary-foreground">
              {spanComments.length > 9 ? "9+" : spanComments.length}
            </div>
          )}
        </div>
      ),
      value: CommentTab.COMMENTS,
      component: (
        <div className="relative flex h-full flex-col rounded-lg bg-background text-card-foreground shadow-sm">
          <div className="flex-1 overflow-auto px-4 pt-2">
            <CommentCards spanUuid={spanUuid} />
          </div>
          <div className="shrink-0">
            <Separator className="mb-2" />
            <AddComment spanUuid={spanUuid} />
          </div>
        </div>
      ),
    },
    {
      label: (
        <div className="flex items-center gap-1">
          <NotebookPen />
          <span>Annotations</span>
          {filteredAnnotations.length > 0 && (
            <div className="absolute -top-0 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-secondary text-xs font-medium text-primary-foreground">
              {filteredAnnotations.length > 9 ? "9+" : filteredAnnotations.length}
            </div>
          )}
        </div>
      ),
      value: CommentTab.ANNOTATIONS,
      component:
        features.annotations && !activeAnnotation ? (
          <div className="h-full overflow-hidden">
            <AnnotationsTable data={filteredAnnotations} />
          </div>
        ) : null,
    },
  ];

  return <TabGroup tabs={tabs} />;
};

export const LilypadPanelTab = ({
  span,
  tab,
  onTabChange,
}: {
  span: SpanMoreDetails;
  tab?: string;
  onTabChange?: (tab: string) => void;
}) => {
  const tabs: Tab[] = [
    {
      label: "Output",
      value: TraceTab.OUTPUT,
      component: span.output ? renderOutput(span.output) : null,
    },
    {
      label: "Response Model",
      value: TraceTab.RESPONSE,
      component: span.response_model ? renderResponseModel(span.response_model) : null,
    },
    {
      label: "Messages",
      value: TraceTab.MESSAGES,
      component: span.messages.length > 0 ? <MessagesContainer messages={span.messages} /> : null,
    },
    {
      label: "Response",
      value: TraceTab.CONTENT,
      component: span.response ? (
        <JsonView shortenTextAfterLength={100} value={span.response} />
      ) : null,
    },
    {
      label: "Prompt Template",
      value: TraceTab.PROMPT_TEMPLATE,
      component: span.template ? (
        <div className="professional p-2 text-sm whitespace-pre-wrap">{span.template}</div>
      ) : null,
    },
    {
      label: "Events",
      value: TraceTab.EVENTS,
      component:
        span.events && span.events.length > 0 ? (
          <div className="h-full overflow-hidden">{renderEventsContainer(span.events)}</div>
        ) : null,
    },
    {
      label: "Metadata",
      value: TraceTab.METADATA,
      component: span.data ? renderMetadata(span.data) : null,
    },
    {
      label: "Data",
      value: TraceTab.DATA,
      component: span.data && (
        <div className="h-full overflow-auto">
          <JsonView value={span.data} />
        </div>
      ),
    },
    {
      label: "Code",
      value: TraceTab.CODE,
      component: span.code ? (
        <CodeBlock language="python" code={span.code} className="h-full overflow-auto" />
      ) : null,
    },
    {
      label: "Signature",
      value: TraceTab.SIGNATURE,
      component: span.signature ? (
        <CodeBlock language="python" code={span.signature} className="h-full overflow-auto" />
      ) : null,
    },
  ];

  return <TabGroup tabs={tabs} tab={tab} handleTabChange={onTabChange} />;
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
            <CardContent className="overflow-x-auto">{event.message}</CardContent>
          </Card>
        ))}
      </CardContent>
    </Card>
  );
};

export const MessagesContainer = ({ messages }: { messages: MessageParam[] }) => {
  const { updateUserConfig, userConfig } = useAuth();
  const defaultMessageRenderer = userConfig?.defaultMessageRenderer ?? "markdown";

  const handleChangeRenderer = (value: "markdown" | "raw") => {
    updateUserConfig({
      defaultMessageRenderer: value,
    });
  };

  return (
    <div className="flex h-full flex-col p-2">
      <div className="flex-grow overflow-auto">
        <div className="flex flex-col gap-4">
          {renderMessagesCard(messages, defaultMessageRenderer)}
        </div>
      </div>

      <div className="mt-2 flex shrink-0 justify-center">
        <div className="inline-flex space-x-1 rounded-md shadow-sm" role="group">
          <Button
            variant={defaultMessageRenderer === "markdown" ? "default" : "outline"}
            size="sm"
            onClick={() => handleChangeRenderer("markdown")}
            className="m-0 rounded-r-none"
          >
            Markdown
          </Button>
          <Button
            variant={defaultMessageRenderer === "raw" ? "default" : "outline"}
            size="sm"
            onClick={() => handleChangeRenderer("raw")}
            className="rounded-l-none"
          >
            Raw
          </Button>
        </div>
      </div>
    </div>
  );
};

const renderResponseModel = (responseModel: any) => {
  if (typeof responseModel === "object") {
    return <JsonView shortenTextAfterLength={100} value={responseModel} />;
  } else {
    return <ReactMarkdown className="professional p-2">{responseModel}</ReactMarkdown>;
  }
};
export const renderOutput = (output: string) => {
  const jsonOutput = safelyParseJSON(output);
  return (
    <>
      {typeof jsonOutput === "object" ? (
        <JsonView shortenTextAfterLength={100} value={jsonOutput} />
      ) : (
        <ReactMarkdown className="professional p-2">{output}</ReactMarkdown>
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
