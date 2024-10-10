import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { marked } from "marked";
import { SpanPublic } from "@/types/types";
import { CodeSnippet } from "@/routes/-codeSnippet";
import { Typography } from "@/components/ui/typography";
import { ArgsCards } from "@/components/ArgsCards";
import DOMPurify from "dompurify";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

export const LilypadPanel = ({ span }: { span: SpanPublic }) => {
  const data = JSON.parse(span.data);
  console.log(data);
  const rawHtml: string = marked.parse(data.attributes["lilypad.output"], {
    async: false,
  });
  const sanitizedHtml = DOMPurify.sanitize(rawHtml);
  return (
    <div className="flex flex-col gap-4">
      <Typography variant="h3">{data.name}</Typography>
      <Card>
        <CardHeader>
          <CardTitle>{"Code"}</CardTitle>
        </CardHeader>
        <CardContent>
          <CodeSnippet code={data.attributes["lilypad.lexical_closure"]} />
        </CardContent>
      </Card>
      <ArgsCards args={JSON.parse(data.attributes["lilypad.arg_values"])} />
      {data.attributes["lilypad.prompt_template"] && (
        <Card>
          <CardHeader>
            <CardTitle>{"Prompt Template"}</CardTitle>
          </CardHeader>
          <CardContent>
            {data.attributes["lilypad.prompt_template"]}
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader>
          <CardTitle>{"Output"}</CardTitle>
        </CardHeader>
        <CardContent
          className="flex"
          dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
        ></CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{"Data"}</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-auto">{JSON.stringify(data, null, 2)}</pre>
        </CardContent>
      </Card>
    </div>
  );
};
