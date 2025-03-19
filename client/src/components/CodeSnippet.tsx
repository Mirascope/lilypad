import { useToast } from "@/hooks/use-toast";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/atom-one-light.min.css";
import { Check, Copy } from "lucide-react";
import { useEffect, useRef, useState } from "react";

// Register the language
hljs.registerLanguage("python", python);

// Custom line numbers function (used in the rendered JSX)
const renderLineNumbers = (code, lineHighlights) => {
  return code.split("\n").map((line, i) => {
    // Line numbers are 1-based, but array indices are 0-based
    const lineNumber = i + 1;
    // Use the custom highlight class or default to a subtle gray background
    const lineClass = lineHighlights[lineNumber] || "bg-gray-50";

    return (
      <div
        key={i}
        className={`hljs-line ${lineClass}`}
        data-line-number={lineNumber}
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
  lineHighlights = {},
}: {
  code: string;
  className?: string;
  showCopyButton?: boolean;
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

    // Add line number styles if they don't exist yet
    if (!document.getElementById("line-number-styles")) {
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
          min-width: 2em;
          text-align: right;
          color: #999;
          user-select: none;
          border-right: 1px solid #ddd;
          margin-right: 0.5em;
        }
        .hljs-line-code {
          flex: 1;
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
  }, [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    toast({ title: "Copied to clipboard" });
    setTimeout(() => setCopied(false), 2000);
  };

  // Format the code with line numbers for display and default to gray background
  const formattedCode = renderLineNumbers(code, lineHighlights);

  return (
    <div className='relative'>
      <pre className={className} ref={preRef}>
        <code
          ref={codeRef}
          className='language-python text-sm overflow-x-auto flex flex-col'
          key={code}
        >
          {formattedCode}
        </code>
      </pre>
      {showCopyButton && (
        <button
          onClick={handleCopy}
          className='absolute top-2 right-2 p-1 rounded bg-gray-200 hover:bg-gray-300 transition-colors'
          aria-label='Copy code'
        >
          {copied ? <Check size={16} /> : <Copy size={16} />}
        </button>
      )}
    </div>
  );
};
