import { ActionsPlugin } from "@/ee/components/lexical/actions-plugin";
import { ClearEditorPlugin } from "@/ee/components/lexical/clear-editor-plugin";
import { CodeHighlightPlugin } from "@/ee/components/lexical/code-highlight-plugin";
import { CollapsibleContainerNode } from "@/ee/components/lexical/collapsible-container-node";
import { CollapsibleContentNode } from "@/ee/components/lexical/collapsible-content-node";
import CollapsiblePlugin from "@/ee/components/lexical/collapsible-plugin";
import { CollapsibleTitleNode } from "@/ee/components/lexical/collapsible-title-node";
import { PLAYGROUND_TRANSFORMERS } from "@/ee/components/lexical/markdown-transformers";
import { TemplateNode } from "@/ee/components/lexical/template-node";
import { TemplatePlugin } from "@/ee/components/lexical/template-plugin";
import { TemplateSuggestionPlugin } from "@/ee/components/lexical/template-suggestion-plugin";
import { ToolbarPlugin } from "@/ee/components/lexical/toolbar-plugin";
import { UneditableParagraphNode } from "@/ee/components/lexical/uneditable-paragraph-node";
import { cn } from "@/lib/utils";
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
import { Ref, RefObject, useMemo } from "react";

export const Editor = ({
  inputs,
  template,
  inputValues,
  editorClassName,
  isDisabled = false,
  isLLM = false,
  placeholderText = "Enter some text...",
  ref,
}: {
  inputs?: string[];
  template?: string;
  inputValues?: Record<string, any>;
  editorClassName?: string;
  isDisabled?: boolean;
  isLLM?: boolean;
  placeholderText?: string;
  ref?: Ref<LexicalEditor>;
}) => {
  const loadContent = () => {
    // 'empty' editor
    const value =
      '{"root":{"children":[{"children":[],"direction":null,"format":"","indent":0,"type":"paragraph","version":1}],"direction":null,"format":"","indent":0,"type":"root","version":1}}';

    return value;
  };
  const editorState = template
    ? () => $convertFromMarkdownString(template, PLAYGROUND_TRANSFORMERS)
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
    [template]
  );
  return (
    <LexicalComposer key={template} initialConfig={config}>
      <div
        className={`flex flex-col border shadow rounded-lg prose max-w-none`}
      >
        {!isDisabled && <ToolbarPlugin isLLM={isLLM} />}

        <div className='relative'>
          <RichTextPlugin
            contentEditable={
              <ContentEditable
                id='prompt-template'
                className={cn(
                  "focus:outline-none w-full px-8 py-4 h-[500px] overflow-auto relative",
                  editorClassName
                )}
              />
            }
            placeholder={
              <p className='text-muted-foreground absolute top-0 px-8 w-full pointer-events-none'>
                {placeholderText}
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
              | RefObject<LexicalEditor | null | undefined>
          }
        />
        <ListPlugin />
        <LinkPlugin />
        {inputs && inputValues !== undefined && (
          <TemplatePlugin inputs={inputs} inputValues={inputValues} />
        )}
        {inputs && inputValues !== undefined && (
          <TemplateSuggestionPlugin inputs={inputs} inputValues={inputValues} />
        )}
        <CodeHighlightPlugin />
        <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
        <CollapsiblePlugin />
        <TabIndentationPlugin />
        <ClearEditorPlugin />
        {isLLM && <ActionsPlugin isDisabled={isDisabled} />}
      </div>
    </LexicalComposer>
  );
};
