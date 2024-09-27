import { CodeHighlightNode, CodeNode } from "@lexical/code";
import { AutoLinkNode, LinkNode } from "@lexical/link";
import { ListItemNode, ListNode } from "@lexical/list";
import { TRANSFORMERS } from "@lexical/markdown";
import {
  InitialConfigType,
  LexicalComposer,
} from "@lexical/react/LexicalComposer";
import exampleTheme from "@/utils/lexical-theme";
import { LexicalErrorBoundary } from "@lexical/react/LexicalErrorBoundary";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { LinkPlugin } from "@lexical/react/LexicalLinkPlugin";
import { ListPlugin } from "@lexical/react/LexicalListPlugin";
import { MarkdownShortcutPlugin } from "@lexical/react/LexicalMarkdownShortcutPlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { HeadingNode, QuoteNode } from "@lexical/rich-text";
import { AutoFocusPlugin } from "@lexical/react/LexicalAutoFocusPlugin";
import { TemplatePlugin } from "@/components/lexical/template-plugin";
import ToolbarPlugin from "@/components/lexical/toolbar-plugin";
import { TableCellNode, TableNode, TableRowNode } from "@lexical/table";
import CodeHighlightPlugin from "@/components/lexical/code-highlight-plugin";
import ActionsPlugin from "@/components/lexical/actions-plugin";

export const Editor = () => {
  const config: InitialConfigType = {
    namespace: "editor",
    theme: exampleTheme,
    nodes: [
      HeadingNode,
      ListNode,
      ListItemNode,
      QuoteNode,
      CodeNode,
      CodeHighlightNode,
      TableNode,
      TableCellNode,
      TableRowNode,
      AutoLinkNode,
      LinkNode,
    ],

    onError: (error) => {
      console.error(error);
    },
  };

  return (
    <LexicalComposer initialConfig={config}>
      <div
        className={`mx-auto relative flex flex-col mt-10 border shadow rounded-lg prose bg-white`}
      >
        <ToolbarPlugin />

        <div className='relative'>
          <RichTextPlugin
            contentEditable={
              <ContentEditable className='focus:outline-none w-full px-8 py-4 h-[500px] overflow-auto relative' />
            }
            placeholder={
              <p className='text-muted-foreground absolute top-0 px-8 py-4 w-full pointer-events-none'>
                Enter some text...
              </p>
            }
            ErrorBoundary={LexicalErrorBoundary}
          />
          <HistoryPlugin />
        </div>
        <TemplatePlugin />
        <ListPlugin />
        <LinkPlugin />
        <CodeHighlightPlugin />
        <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
      </div>
      <ActionsPlugin />
    </LexicalComposer>
  );
};
