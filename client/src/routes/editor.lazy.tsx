import { createLazyFileRoute } from "@tanstack/react-router";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import { Editor } from "@/routes/-editor";
hljs.registerLanguage("python", python);

export const Route = createLazyFileRoute("/editor")({
  component: () => (
    <div className='bg-secondary h-screen lexical'>
      <Editor />
    </div>
  ),
});
