import { useAuth } from "@/auth";
import { CodeSnippet } from "@/components/CodeSnippet";
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
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { AnnotationView } from "@/ee/components/annotations/AnnotationView";
import { AnnotationsTable } from "@/ee/components/AnnotationsTable";
import { annotationsBySpanQueryOptions } from "@/ee/utils/annotations";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { CommentTab, Tab, TraceTab } from "@/types/traces";
import {
  AnnotationPublic,
  Event,
  MessageParam,
  SpanMoreDetails,
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
      <CardContent className="overflow-x-auto px-4 font-default">
        {content}
      </CardContent>
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

export const SpanComments = ({
  projectUuid,
  spanUuid,
  activeAnnotation,
  path,
}: {
  projectUuid: string;
  spanUuid: string;
  activeAnnotation?: AnnotationPublic | null;
  path?: string;
}) => {
  const features = useFeatureAccess();
  const { data: spanComments } = useSuspenseQuery(
    commentsBySpanQueryOptions(spanUuid)
  );
  const { data: annotations } = useSuspenseQuery(
    annotationsBySpanQueryOptions(projectUuid, spanUuid, features.annotations)
  );
  const filteredAnnotations = annotations.filter(
    (annotation) => annotation.label
  );

  const tabs: Tab[] = [
    {
      label: "Annotate",
      value: CommentTab.ANNOTATE,
      component:
        features.annotations && activeAnnotation ? (
          <AnnotationView annotation={activeAnnotation} path={path} />
        ) : null,
    },
    {
      label: (
        <div className="flex items-center gap-1">
          <MessageSquareMore />
          <span>Discussion</span>
          {spanComments.length > 0 && (
            <div className="absolute -top-0 -right-2 bg-secondary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {spanComments.length > 9 ? "9+" : spanComments.length}
            </div>
          )}
        </div>
      ),
      value: CommentTab.COMMENTS,
      component: (
        <div className="bg-primary-foreground text-card-foreground relative flex flex-col rounded-lg shadow-sm h-full">
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
            <div className="absolute -top-0 -right-2 bg-secondary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {filteredAnnotations.length > 9
                ? "9+"
                : filteredAnnotations.length}
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
      component: span.output ? (
        <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg shadow-sm overflow-auto h-full">
          {renderOutput(span.output)}
        </div>
      ) : null,
    },
    {
      label: "Prompt Template",
      value: TraceTab.PROMPT_TEMPLATE,
      component: span.template ? (
        <div className="p-2 whitespace-pre-wrap text-sm font-default">
          {span.template}
        </div>
      ) : null,
    },
    {
      // TODO: Use TabGroup for Markdown / Plaintext and put it at the bottom sticky
      label: "Messages",
      value: TraceTab.MESSAGES,
      component:
        span.messages.length > 0 ? (
          <MessagesContainer messages={span.messages} />
        ) : null,
    },
    {
      label: "Events",
      value: TraceTab.EVENTS,
      component:
        span.events && span.events.length > 0 ? (
          <div className="h-full overflow-hidden">
            {renderEventsContainer(span.events)}
          </div>
        ) : null,
    },
    {
      label: "Metadata",
      value: TraceTab.METADATA,
      component: span.data ? (
        <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg shadow-sm overflow-auto h-full">
          {renderMetadata(span.data)}
        </div>
      ) : null,
    },
    {
      label: "Data",
      value: TraceTab.DATA,
      component: span.data && (
        <div className="h-full overflow-auto">
          <div className="bg-primary-foreground p-2 text-card-foreground relative rounded-lg shadow-sm overflow-auto h-full">
            <JsonView value={span.data} />
          </div>
        </div>
      ),
    },
    {
      label: "Code",
      value: TraceTab.CODE,
      component: span.code ? (
        <CodeSnippet code={span.code} className="h-full" />
      ) : null,
    },
    {
      label: "Signature",
      value: TraceTab.SIGNATURE,
      component: span.signature ? (
        <CodeSnippet code={span.signature} className="h-full" />
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
    <>
      <Switch
        checked={defaultMessageRenderer === "markdown"}
        onCheckedChange={handleChange}
      />
      <div className="flex flex-col gap-4">
        {renderMessagesCard(messages, defaultMessageRenderer)}
      </div>
    </>
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
