import { ArgsCards } from "@/components/ArgsCards";
import { CodeSnippet } from "@/components/CodeSnippet";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Typography } from "@/components/ui/typography";
import {
  renderCardOutput,
  renderData,
  renderEventsContainer,
  renderMessagesContainer,
  renderMetadata,
} from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import JsonView, { JsonViewProps } from "@uiw/react-json-view";
import hljs from "highlight.js/lib/core";
import markdown from "highlight.js/lib/languages/markdown";
import python from "highlight.js/lib/languages/python";
import { JSX } from "react";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

interface Tab {
  label: string;
  value: string;
  component?: JSX.Element | null;
}

export const LilypadPanel = ({
  spanUuid,
  showJsonArgs,
  dataProps,
}: {
  spanUuid: string;
  showJsonArgs?: boolean;
  dataProps?: JsonViewProps<object>;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const tabs: Tab[] = [
    {
      label: "Code",
      value: "code",
      component: <CodeSnippet code={span.code ?? ""} />,
    },
    {
      label: "Signature",
      value: "signature",
      component: <CodeSnippet code={span.signature ?? ""} />,
    },
  ];
  const data: Record<string, unknown> = span.data as Record<string, unknown>;
  const attributes: Record<string, string> | undefined =
    data.attributes as Record<string, string>;
  const lilypadType = attributes?.["lilypad.type"];
  const versionNum = attributes?.[`lilypad.${lilypadType}.version`];
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>
        {span.display_name} {versionNum && `v${versionNum}`}
      </Typography>
      <div className='flex gap-1 flex-wrap'>
        {span.input_tokens != 0 &&
          span.input_tokens &&
          span.output_tokens != 0 &&
          span.output_tokens && (
            <Badge className='text-xs font-medium m-0'>
              <span>{span.input_tokens}</span>
              <span className='mx-1'>&#8594;</span>
              <span>{span.output_tokens}</span>
              <span className='mx-1'>=</span>
              <span>{span.input_tokens + span.output_tokens}</span>
            </Badge>
          )}
        {span.cost != 0 && span.cost && <Badge>${span.cost.toFixed(5)}</Badge>}
        {span.duration_ms && (
          <Badge>{(span.duration_ms / 1_000_000_000).toFixed(3)}s</Badge>
        )}
      </div>
      {(span.code ?? span.signature) && (
        <Card>
          <CardHeader>
            <CardTitle>{"Code"}</CardTitle>
          </CardHeader>
          <CardContent className='overflow-x-auto'>
            <Tabs defaultValue='code' className='w-full'>
              <div className='flex w-full'>
                <TabsList className={`w-[160px]`}>
                  {tabs.map((tab) => (
                    <TabsTrigger key={tab.value} value={tab.value}>
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
          </CardContent>
        </Card>
      )}
      {span.events &&
        span.events.length > 0 &&
        renderEventsContainer(span.events)}
      {span.arg_values &&
        (showJsonArgs ? (
          <Card>
            <CardHeader>
              <CardTitle>{"Input"}</CardTitle>
            </CardHeader>
            <CardContent className='flex flex-col'>
              <JsonView value={span.arg_values} />
            </CardContent>
          </Card>
        ) : (
          <ArgsCards args={span.arg_values} />
        ))}
      {span.template && (
        <Card>
          <CardHeader>
            <CardTitle>{"Prompt Template"}</CardTitle>
          </CardHeader>
          <CardContent className='whitespace-pre-wrap'>
            {span.template}
          </CardContent>
        </Card>
      )}
      {span.messages.length > 0 && renderMessagesContainer(span.messages)}
      {renderCardOutput(span.output)}
      {renderMetadata(span.data)}
      {renderData({
        value: span.data,
        ...dataProps,
      })}
    </div>
  );
};

// const TagPopover = () => {
//   const { data: tags } = useSuspenseQuery(tagsQueryOptions());
//   const createTag = useCreateTagMutation();
//   const [spanTags, setSpanTags] = useState<string[] | null>(null);
//   const handleTagChange = (values: string[]) => {
//     setSpanTags(values);
//   };
//   return (
//     <Combobox
//       multiple={true}
//       customTrigger={
//         <Button size='icon' variant='outline'>
//           <Plus />
//         </Button>
//       }
//       items={tags.map((tag) => ({
//         value: tag.uuid,
//         label: tag.name,
//       }))}
//       value={spanTags ?? []}
//       onChange={(values: string[]) => setSpanTags(values)}
//     />
//   );
// };
