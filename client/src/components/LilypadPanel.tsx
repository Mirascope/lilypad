import { ArgsCards } from "@/components/ArgsCards";
import { CodeSnippet } from "@/components/CodeSnippet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Typography } from "@/components/ui/typography";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import JsonView from "@uiw/react-json-view";
import hljs from "highlight.js/lib/core";
import markdown from "highlight.js/lib/languages/markdown";
import python from "highlight.js/lib/languages/python";
import ReactMarkdown from "react-markdown";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};

export const LilypadPanel = ({ spanUuid }: { spanUuid: string }) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const tabs: Tab[] = [
    {
      label: "Signature",
      value: "signature",
      component: <CodeSnippet code={span.signature || ""} />,
    },
    {
      label: "Code",
      value: "code",
      component: <CodeSnippet code={span.code || ""} />,
    },
  ];
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{span.display_name}</Typography>
      <Card>
        <CardHeader>
          <CardTitle>{"Code"}</CardTitle>
        </CardHeader>
        <CardContent className='overflow-x-auto'>
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
      {span.arg_values && <ArgsCards args={span.arg_values} />}
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
      {span.output && (
        <Card>
          <CardHeader>
            <CardTitle>{"Output"}</CardTitle>
          </CardHeader>
          <CardContent className='flex flex-col'>
            <ReactMarkdown>{span.output}</ReactMarkdown>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader>
          <CardTitle>{"Data"}</CardTitle>
        </CardHeader>
        {span.data && (
          <CardContent className='overflow-x-auto'>
            <JsonView value={span.data} />
          </CardContent>
        )}
      </Card>
    </div>
  );
};
