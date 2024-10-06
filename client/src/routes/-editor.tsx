import { CodeHighlightNode, CodeNode } from "@lexical/code";
import { LinkNode } from "@lexical/link";
import { ListItemNode, ListNode } from "@lexical/list";
import { TRANSFORMERS } from "@lexical/markdown";
import {
  InitialConfigType,
  LexicalComposer,
} from "@lexical/react/LexicalComposer";
import exampleTheme from "@/utils/lexical-theme";
import { CustomDataSuggestionPlugin } from "@/components/lexical/custom-data-plugin";
import { TemplateNode } from "@/components/lexical/template-node";
import { LexicalErrorBoundary } from "@lexical/react/LexicalErrorBoundary";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { LinkPlugin } from "@lexical/react/LexicalLinkPlugin";
import { ListPlugin } from "@lexical/react/LexicalListPlugin";
import { MarkdownShortcutPlugin } from "@lexical/react/LexicalMarkdownShortcutPlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { HeadingNode, QuoteNode } from "@lexical/rich-text";
import ToolbarPlugin from "@/components/lexical/toolbar-plugin";
import { TableCellNode, TableNode, TableRowNode } from "@lexical/table";
import { CodeHighlightPlugin } from "@/components/lexical/code-highlight-plugin";
import { CollapsibleContainerNode } from "@/components/lexical/collapsible-container-node";
import { CollapsibleContentNode } from "@/components/lexical/collapsible-content-node";
import { CollapsibleTitleNode } from "@/components/lexical/collapsible-title-node";
import CollapsiblePlugin from "@/components/lexical/collapsible-plugin";
import { UneditableParagraphNode } from "@/components/lexical/uneditable-paragraph-node";
import { forwardRef, useMemo } from "react";
import { EditorRefPlugin } from "@lexical/react/LexicalEditorRefPlugin";
import { TemplatePlugin } from "@/components/lexical/template-plugin";
export const Editor = forwardRef(
  (
    { inputs, editorState }: { inputs: string[]; editorState: string },
    ref: any
  ) => {
    const config = useMemo(
      () => ({
        namespace: "editor",
        editorState: editorState,
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
          LinkNode,
          TemplateNode,
          CollapsibleContainerNode,
          CollapsibleContentNode,
          CollapsibleTitleNode,
          UneditableParagraphNode,
        ],
        onError: (error) => {
          console.error(error);
        },
      }),
      []
    );
    return (
      <LexicalComposer initialConfig={config}>
        <div className={`flex flex-col border shadow rounded-lg prose`}>
          <ToolbarPlugin />

          <div className='relative'>
            <RichTextPlugin
              contentEditable={
                <ContentEditable
                  id='prompt-template'
                  className='focus:outline-none w-full px-8 py-4 h-[500px] overflow-auto relative'
                />
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
          <EditorRefPlugin editorRef={ref} />
          <ListPlugin />
          <LinkPlugin />
          {inputs && <TemplatePlugin inputs={inputs} />}
          {inputs && <CustomDataSuggestionPlugin inputs={inputs} />}
          <CodeHighlightPlugin />
          <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
          {/* TODO: Fix too many rerenders */}
          <CollapsiblePlugin />
        </div>
      </LexicalComposer>
    );
  }
);
