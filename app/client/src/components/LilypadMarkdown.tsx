import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
interface MarkdownRendererProps {
  content: string;
}

export const LilypadMarkdown = ({ content }: MarkdownRendererProps) => {
  return (
    <div className="prose dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkBreaks]}>{content}</ReactMarkdown>
    </div>
  );
};
