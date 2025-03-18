import { useToast } from "@/hooks/use-toast";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/atom-one-light.min.css";
import { Check, Copy } from "lucide-react";
import { ReactNode, useEffect, useRef, useState } from "react";
hljs.registerLanguage("python", python);

export interface CodeSnippetProps {
  code: string;
  className?: string;
  showCopyButton?: boolean;
  showLineNumbers?: boolean;
  customLineNumbers?: ReactNode;
  lineHighlights?: Record<number, string>; // Maps line number to CSS class for highlighting
  wrapperClassName?: string;
}

export const CodeSnippet = ({
  code,
  className = "",
  showCopyButton = true,
  showLineNumbers = false,
  customLineNumbers,
  lineHighlights = {},
  wrapperClassName = "",
}: CodeSnippetProps) => {
  const codeRef = useRef<HTMLElement>(null);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (!codeRef.current) return;
    // Prevents warning about highlighting the same element multiple times
    if (!codeRef.current.getAttribute("data-highlighted")) {
      // Highlights the code snippet
      hljs.highlightElement(codeRef.current);
    }
  }, [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    toast({ title: "Copied to clipboard" });
    setTimeout(() => setCopied(false), 2000);
  };

  // Generate line numbers if needed
  const renderLineNumbers = () => {
    if (customLineNumbers) {
      return customLineNumbers;
    }

    if (showLineNumbers) {
      const lines = code.split("\n");
      return (
        <div className='flex-none w-12 text-right pr-2 bg-gray-100 border-r border-gray-300'>
          {lines.map((_, index) => (
            <div
              key={`line-${index + 1}`}
              className='text-xs leading-5 text-gray-500 py-[1px]'
            >
              {index + 1}
            </div>
          ))}
        </div>
      );
    }

    return null;
  };

  // Apply line highlights if provided
  const renderCode = () => {
    if (Object.keys(lineHighlights).length > 0) {
      const lines = code.split("\n");
      return (
        <pre className={`flex-grow !bg-transparent ${className}`}>
          {lines.map((line, index) => {
            const highlightClass = lineHighlights[index + 1] || "";
            return (
              <div
                key={`highlight-line-${index + 1}`}
                className={`${highlightClass}`}
              >
                <code>{line}</code>
              </div>
            );
          })}
        </pre>
      );
    }

    return (
      <pre className={className}>
        <code
          ref={codeRef}
          className='language-python text-sm overflow-x-auto'
          key={code}
        >
          {code}
        </code>
      </pre>
    );
  };

  return (
    <div className={`relative font-mono ${wrapperClassName}`}>
      {showLineNumbers || customLineNumbers ? (
        <div className='flex'>
          {renderLineNumbers()}
          {renderCode()}
        </div>
      ) : (
        renderCode()
      )}

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
