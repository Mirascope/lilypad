import { CodeHighlightNode, CodeNode } from "@lexical/code";
import { LinkNode } from "@lexical/link";
import { ListItemNode, ListNode } from "@lexical/list";
import { $convertFromMarkdownString, TRANSFORMERS } from "@lexical/markdown";
import { LexicalComposer } from "@lexical/react/LexicalComposer";
import exampleTheme from "@/utils/lexical-theme";
import { CustomDataSuggestionPlugin } from "@/components/lexical/custom-data-plugin";
import { TemplateNode } from "@/components/lexical/template-node";
import { LexicalErrorBoundary } from "@lexical/react/LexicalErrorBoundary";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { LinkPlugin } from "@lexical/react/LexicalLinkPlugin";
import { ListPlugin } from "@lexical/react/LexicalListPlugin";
import { TabIndentationPlugin } from "@lexical/react/LexicalTabIndentationPlugin";
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
import { ForwardedRef, forwardRef, useMemo } from "react";
import { EditorRefPlugin } from "@lexical/react/LexicalEditorRefPlugin";
import { TemplatePlugin } from "@/components/lexical/template-plugin";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { LexicalEditor } from "lexical";
export const Editor = forwardRef(
  (
    { inputs, promptTemplate }: { inputs: string[]; promptTemplate: string },
    ref: ForwardedRef<LexicalEditor>
  ) => {
    const loadContent = () => {
      // 'empty' editor
      const value =
        '{"root":{"children":[{"children":[],"direction":null,"format":"","indent":0,"type":"paragraph","version":1}],"direction":null,"format":"","indent":0,"type":"root","version":1}}';

      return value;
    };
    const editorState = promptTemplate
      ? () =>
          $convertFromMarkdownString(promptTemplate, PLAYGROUND_TRANSFORMERS)
      : loadContent();
    const config = useMemo(
      () => ({
        namespace: "editor",
        editorState,
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
        onError: (error: Error) => {
          console.error(error);
        },
      }),
      [promptTemplate]
    );
    return (
      <LexicalComposer key={promptTemplate} initialConfig={config}>
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
                <p className='text-muted-foreground absolute top-0 px-8 w-full pointer-events-none'>
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
          <CollapsiblePlugin />
          <TabIndentationPlugin />
        </div>
      </LexicalComposer>
    );
  }
);
