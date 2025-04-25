import { TagPopover } from "@/components/TagPopover";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import {
  renderCardOutput,
  renderData,
  renderEventsContainer,
  renderMessagesContainer,
  renderMetadata,
  TraceCodeTab,
} from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import JsonView, { JsonViewProps } from "@uiw/react-json-view";
import hljs from "highlight.js/lib/core";
import markdown from "highlight.js/lib/languages/markdown";
import python from "highlight.js/lib/languages/python";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

export const LilypadPanel = ({
  spanUuid,
  dataProps,
}: {
  spanUuid: string;
  dataProps?: JsonViewProps<object>;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
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
        {span.tags?.map((tag) => (
          <Badge pill variant='outline' size='lg' key={tag.uuid}>
            {tag.name}
          </Badge>
        ))}
        {span.project_uuid && (
          <TagPopover
            spanUuid={span.uuid}
            projectUuid={span.project_uuid}
            key='add-tag'
          />
        )}
      </div>
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
      {span.events &&
        span.events.length > 0 &&
        renderEventsContainer(span.events)}
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
      <div className='flex gap-4 flex-wrap'>
        {span.arg_values && (
          <Card className='w-[calc(50%-0.5rem)] min-w-[300px] flex-grow'>
            <CardHeader>
              <CardTitle>{"Input"}</CardTitle>
            </CardHeader>
            <CardContent className='overflow-x-auto'>
              <JsonView value={span.arg_values} />
            </CardContent>
          </Card>
        )}
        {span.output && (
          <Card className='w-[calc(50%-0.5rem)] min-w-[300px] flex-grow'>
            {renderCardOutput(span.output)}
          </Card>
        )}
      </div>
      <TraceCodeTab span={span} />
      {renderMetadata(span.data)}
      {renderData({
        value: span.data,
        ...dataProps,
      })}
    </div>
  );
};
