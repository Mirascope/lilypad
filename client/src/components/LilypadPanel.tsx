import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { SpanPublic } from "@/types/types";
import { CodeSnippet } from "@/components/CodeSnippet";
import { Typography } from "@/components/ui/typography";
import { ArgsCards } from "@/components/ArgsCards";
import ReactMarkdown from "react-markdown";
import JsonView from "@uiw/react-json-view";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

interface InstrumentationScope {
  attributes: object;
  name: string;
  schema_url: string;
  version: string;
}
interface SpanData {
  name: string;
  attributes: Record<string, any>;
  end_time: number;
  start_time: number;
  events: any[];
  links: any[];
  instrumentation_scope: InstrumentationScope;
  parent_span_id: string;
  resource: string;
  span_id: string;
  status: string;
  trace_id: string;
}

export const LilypadPanel = ({ span }: { span: SpanPublic }) => {
  const data = span.data as SpanData;
  const attributes = data.attributes;
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{data.name}</Typography>
      <Card>
        <CardHeader>
          <CardTitle>{"Code"}</CardTitle>
        </CardHeader>
        <CardContent>
          <CodeSnippet code={data.attributes["lilypad.generation.signature"]} />
        </CardContent>
      </Card>
      <ArgsCards
        args={JSON.parse(data.attributes["lilypad.generation.arg_values"])}
      />
      {data.attributes["lilypad.generation.prompt_template"] && (
        <Card>
          <CardHeader>
            <CardTitle>{"Prompt Template"}</CardTitle>
          </CardHeader>
          <CardContent className='whitespace-pre-wrap'>
            {data.attributes["lilypad.generation.prompt_template"]}
          </CardContent>
        </Card>
      )}
      {data.attributes["lilypad.generation.output"] && (
        <Card>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex flex-col'>
            <ReactMarkdown>
              {data.attributes["lilypad.generation.output"]}
            </ReactMarkdown>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader>
          <CardTitle>{"Data"}</CardTitle>
        </CardHeader>
        {data && (
          <CardContent>
            <JsonView value={data} />
          </CardContent>
        )}
      </Card>
    </div>
  );
};
