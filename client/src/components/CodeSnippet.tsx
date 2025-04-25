import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/atom-one-light.min.css";
import { Check, Copy } from "lucide-react";
import { useEffect, useRef, useState } from "react";

// Register the language
hljs.registerLanguage("python", python);

const renderCode = (
  code: string,
  showLineNumbers: boolean,
  lineHighlights: Record<string, string>
) => {
  const lines = code.split("\n");
  // Calculate the number of digits in the maximum line number
  const maxLineNumber = lines.length;
  const digits = maxLineNumber.toString().length;

  if (!showLineNumbers) {
    // If line numbers are disabled, just return the code with highlighting
    return lines.map((line, i) => {
      // Line numbers are 1-based, but array indices are 0-based
      const lineNumber = i + 1;
      const lineClass = lineHighlights[lineNumber] || "bg-gray-50";

      return (
        <div key={i} className={`hljs-line ${lineClass} w-full`}>
          <span className='hljs-line-code'>{line}</span>
        </div>
      );
    });
  }

  // Return with line numbers
  return lines.map((line, i) => {
    // Line numbers are 1-based, but array indices are 0-based
    const lineNumber = i + 1;
    const lineClass = lineHighlights[lineNumber] || "bg-gray-50";

    return (
      <div
        key={i}
        className={`hljs-line ${lineClass} w-full`}
        data-line-number={lineNumber}
        data-digits={digits}
      >
        <span className='hljs-line-number'>{lineNumber}</span>
        <span className='hljs-line-code'>{line}</span>
      </div>
    );
  });
};

export const CodeSnippet = ({
  code,
  className,
  showCopyButton = true,
  showLineNumbers = true,
  lineHighlights = {},
}: {
  code: string;
  className?: string;
  showCopyButton?: boolean;
  showLineNumbers?: boolean;
  lineHighlights?: Record<string, string>;
}) => {
  const preRef = useRef<HTMLPreElement>(null);
  const codeRef = useRef<HTMLElement>(null);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (!codeRef.current) return;

    // We need to highlight each line separately
    const codeLines = codeRef.current.querySelectorAll(".hljs-line-code");

    codeLines.forEach((line) => {
      if (!line.hasAttribute("data-highlighted")) {
        hljs.highlightElement(line as HTMLElement);
      }
    });

    // Add line number styles if they don't exist yet and line numbers are shown
    if (showLineNumbers && !document.getElementById("line-number-styles")) {
      const digits = code.split("\n").length.toString().length;
      const styleEl = document.createElement("style");
      styleEl.id = "line-number-styles";
      styleEl.textContent = `
        .hljs-line {
          display: flex;
          width: 100%;
        }
        .hljs-line-number {
          display: inline-block;
          padding-right: 1em;
          min-width: ${digits + 1}em;
          text-align: right;
          color: #999;
          user-select: none;
          border-right: 1px solid #ddd;
          margin-right: 0.5em;
        }
        .hljs-line[data-digits="2"] .hljs-line-number {
          min-width: 3em;
        }
        .hljs-line[data-digits="3"] .hljs-line-number {
          min-width: 4em;
        }
        .hljs-line-code {
          flex: 1;
          word-break: break-all;
          white-space: pre-wrap;
          background: transparent !important; /* Ensure HLJS doesn't override our backgrounds */
        }
        /* Ensure our custom highlighting takes precedence */
        .hljs-line.bg-green-100 .hljs-line-code,
        .hljs-line.bg-yellow-100 .hljs-line-code,
        .hljs-line.bg-red-100 .hljs-line-code,
        .hljs-line.bg-blue-100 .hljs-line-code,
        .hljs-line.bg-purple-100 .hljs-line-code,
        .hljs-line[class*="bg-"] .hljs-line-code {
          background: inherit !important;
        }
      `;
      document.head.appendChild(styleEl);
    }
  }, [code, showLineNumbers]);

  const handleCopy = () => {
    navigator.clipboard
      .writeText(code)
      .then(() => {
        setCopied(true);
        toast({ title: "Copied to clipboard" });
        setTimeout(() => setCopied(false), 2000);
      })
      .catch((error: unknown) => {
        if (error instanceof Error) {
          toast({
            title: "Failed to copy",
            description: error.message,
            variant: "destructive",
          });
        } else {
          toast({
            title: "Failed to copy",
            variant: "destructive",
          });
        }
      });
  };

  const formattedCode = renderCode(code, showLineNumbers, lineHighlights);

  return (
    <div className='relative w-full overflow-x-auto'>
      <pre
        className={cn("whitespace-pre overflow-visible", className)}
        ref={preRef}
      >
        <code
          ref={codeRef}
          className='language-python text-sm flex flex-col w-full'
          key={code}
        >
          {formattedCode}
        </code>
      </pre>
      {showCopyButton && (
        <Button
          variant='outline'
          size='icon'
          onClick={handleCopy}
          className='w-6 h-6 absolute top-2 right-2 p-1 rounded bg-gray-200 hover:bg-gray-300 transition-colors'
          aria-label='Copy code'
        >
          {copied ? <Check size={16} /> : <Copy size={16} />}
        </Button>
      )}
    </div>
  );
};
