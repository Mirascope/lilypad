import { CodeHighlightPlugin } from "@/components/lexical/code-highlight-plugin";
import { CollapsibleContainerNode } from "@/components/lexical/collapsible-container-node";
import { CollapsibleContentNode } from "@/components/lexical/collapsible-content-node";
import CollapsiblePlugin from "@/components/lexical/collapsible-plugin";
import { CollapsibleTitleNode } from "@/components/lexical/collapsible-title-node";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { TemplateNode } from "@/components/lexical/template-node";
import { TemplatePlugin } from "@/components/lexical/template-plugin";
import { TemplateSuggestionPlugin } from "@/components/lexical/template-suggestion-plugin";
import ToolbarPlugin from "@/components/lexical/toolbar-plugin";
import { UneditableParagraphNode } from "@/components/lexical/uneditable-paragraph-node";
import exampleTheme from "@/utils/lexical-theme";
import { CodeHighlightNode, CodeNode } from "@lexical/code";
import { LinkNode } from "@lexical/link";
import { ListItemNode, ListNode } from "@lexical/list";
import { $convertFromMarkdownString, TRANSFORMERS } from "@lexical/markdown";
import { LexicalComposer } from "@lexical/react/LexicalComposer";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { EditorRefPlugin } from "@lexical/react/LexicalEditorRefPlugin";
import { LexicalErrorBoundary } from "@lexical/react/LexicalErrorBoundary";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { LinkPlugin } from "@lexical/react/LexicalLinkPlugin";
import { ListPlugin } from "@lexical/react/LexicalListPlugin";
import { MarkdownShortcutPlugin } from "@lexical/react/LexicalMarkdownShortcutPlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { TabIndentationPlugin } from "@lexical/react/LexicalTabIndentationPlugin";
import { HeadingNode, QuoteNode } from "@lexical/rich-text";
import { TableCellNode, TableNode, TableRowNode } from "@lexical/table";
import { LexicalEditor } from "lexical";
import { ForwardedRef, forwardRef, MutableRefObject, useMemo } from "react";
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
          <EditorRefPlugin
            editorRef={
              ref as
                | ((instance: LexicalEditor | null) => void)
                | MutableRefObject<LexicalEditor | null | undefined>
            }
          />
          <ListPlugin />
          <LinkPlugin />
          {inputs && <TemplatePlugin inputs={inputs} />}
          {inputs && <TemplateSuggestionPlugin inputs={inputs} />}
          <CodeHighlightPlugin />
          <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
          <CollapsiblePlugin />
          <TabIndentationPlugin />
        </div>
      </LexicalComposer>
    );
  }
);
