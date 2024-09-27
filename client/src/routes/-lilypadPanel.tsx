import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import markdown from "highlight.js/lib/languages/markdown";
import { marked } from "marked";
import { SpanPublic } from "@/types/types";
import { CodeSnippet } from "@/routes/-codeSnippet";
import { Typography } from "@/components/ui/typography";
import DOMPurify from "dompurify";
hljs.registerLanguage("python", python);
hljs.registerLanguage("markdown", markdown);

export const LilypadPanel = ({ span }: { span: SpanPublic }) => {
  const data = JSON.parse(span.data);
  const inputValues = JSON.parse(data.attributes["lilypad.input_values"]);
  const rawHtml: string = marked.parse(data.attributes["lilypad.output"], {
    async: false,
  });
  const sanitizedHtml = DOMPurify.sanitize(rawHtml);
  return (
    <div className='flex flex-col gap-4'>
      <Typography variant='h3'>{data.name}</Typography>
      <Card>
        <CardHeader>
          <CardTitle>{"Code"}</CardTitle>
        </CardHeader>
        <CardContent>
          <CodeSnippet code={data.attributes["lilypad.lexical_closure"]} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{"Inputs"}</CardTitle>
        </CardHeader>
        <CardContent className='flex'>
          {Object.entries(inputValues).map(([key, value]) => (
            <Card key={key}>
              <CardHeader>
                <CardTitle>{key}</CardTitle>
              </CardHeader>
              <CardContent>{`${value}`}</CardContent>
            </Card>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{"Output"}</CardTitle>
        </CardHeader>
        <CardContent
          className='flex'
          dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
        ></CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{"Data"}</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className='overflow-auto'>{JSON.stringify(data, null, 2)}</pre>
        </CardContent>
      </Card>
    </div>
  );
};
