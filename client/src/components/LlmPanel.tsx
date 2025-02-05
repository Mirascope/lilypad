import { Badge } from "@/components/ui/badge";
import { Typography } from "@/components/ui/typography";
import { renderData, renderMessagesContainer } from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import hljs from "highlight.js/lib/core";
import markdown from "highlight.js/lib/languages/markdown";
import python from "highlight.js/lib/languages/python";

hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

export const LlmPanel = ({ spanUuid }: { spanUuid: string }) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));

  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{span.display_name}</Typography>
      <div className='flex gap-1 flex-wrap'>
        <Badge>{span.provider}</Badge>
        <Badge>{span.model}</Badge>
        {span.input_tokens && span.output_tokens && (
          <Badge className='text-xs font-medium m-0'>
            <span>{span.input_tokens}</span>
            <span className='mx-1'>&#8594;</span>
            <span>{span.output_tokens}</span>
            <span className='mx-1'>=</span>
            <span>{span.input_tokens + span.output_tokens}</span>
          </Badge>
        )}
        {span.cost && <Badge>${span.cost.toFixed(5)}</Badge>}
        <Badge>{(span.duration_ms / 1_000_000_000).toFixed(3)}s</Badge>
      </div>
      {span.messages.length > 0 && renderMessagesContainer(span.messages)}
      {renderData(span.data)}
    </div>
  );
};
