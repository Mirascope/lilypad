import { ArgsCards } from "@/components/ArgsCards";
import { CodeSnippet } from "@/components/CodeSnippet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Typography } from "@/components/ui/typography";
import {
  renderData,
  renderMessagesContainer,
  renderOutput,
} from "@/utils/panel-utils";
import { spanQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import hljs from "highlight.js/lib/core";
import markdown from "highlight.js/lib/languages/markdown";
import python from "highlight.js/lib/languages/python";
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
      label: "Code",
      value: "code",
      component: <CodeSnippet code={span.code || ""} />,
    },
    {
      label: "Signature",
      value: "signature",
      component: <CodeSnippet code={span.signature || ""} />,
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
      {span.messages.length > 0 && renderMessagesContainer(span.messages)}
      {renderOutput(span.output)}
      {renderData(span.data)}
    </div>
  );
};
