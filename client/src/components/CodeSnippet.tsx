import { useToast } from "@/hooks/use-toast";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/atom-one-light.min.css";
import { Check, Copy } from "lucide-react";
import { useEffect, useRef, useState } from "react";
hljs.registerLanguage("python", python);

export const CodeSnippet = ({
  code,
  className,
  showCopyButton = true,
}: {
  code: string;
  className?: string;
  showCopyButton?: boolean;
}) => {
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

  return (
    <div className='relative'>
      <pre className={className}>
        <code
          ref={codeRef}
          className='language-python text-sm overflow-x-auto'
          key={code}
        >
          {code}
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
