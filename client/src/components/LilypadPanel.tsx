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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};
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
  const type = attributes["lilypad.type"];
  const signature = attributes[`lilypad.${type}.signature`];
  const code = attributes[`lilypad.${type}.code`];
  const template = attributes[`lilypad.${type}.template`];
  const output = attributes[`lilypad.${type}.output`];
  let argValues = {};
  try {
    argValues = JSON.parse(attributes[`lilypad.${type}.arg_values`]);
  } catch (e) {
    argValues = {};
  }
  const tabs: Tab[] = [
    {
      label: "Signature",
      value: "signature",
      component: <CodeSnippet code={signature} />,
    },
    {
      label: "Code",
      value: "code",
      component: <CodeSnippet code={code} />,
    },
  ];
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{data.name}</Typography>
      <Card>
        <CardHeader>
          <CardTitle>{"Code"}</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue='signature' className='w-full'>
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
      <ArgsCards args={argValues} />
      {template && (
        <Card>
          <CardHeader>
            <CardTitle>{"Prompt Template"}</CardTitle>
          </CardHeader>
          <CardContent className='whitespace-pre-wrap'>{template}</CardContent>
        </Card>
      )}
      {output && (
        <Card>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex flex-col'>
            <ReactMarkdown>{output}</ReactMarkdown>
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
