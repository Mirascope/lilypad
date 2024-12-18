import { useEffect, useRef } from "react";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/atom-one-light.min.css";
hljs.registerLanguage("python", python);

export const CodeSnippet = ({ code }: { code: string }) => {
  const codeRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!codeRef.current) return;
    // Prevents warning about highlighting the same element multiple times
    if (!codeRef.current.getAttribute("data-highlighted")) {
      // Highlights the code snippet
      hljs.highlightElement(codeRef.current);
    }
  }, [code]);
  return (
    <pre>
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
