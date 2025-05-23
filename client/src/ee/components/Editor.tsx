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
  placeholderClassName,
  isDisabled = false,
  isLLM = false,
  placeholderText = "Enter some text...",
  ref,
}: {
  inputs?: string[];
  template?: string;
  inputValues?: Record<string, any>;
  editorClassName?: string;
  placeholderClassName?: string;
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
      <div className={`prose flex max-w-none flex-col rounded-lg border shadow dark:prose-invert`}>
        {!isDisabled && isLLM && <ToolbarPlugin />}

        <div className="relative">
          <RichTextPlugin
            contentEditable={
              <ContentEditable
                id="prompt-template"
                className={cn(
                  "relative h-[500px] w-full overflow-auto px-8 py-4 focus:outline-none",
                  editorClassName
                )}
              />
            }
            placeholder={
              <p
                className={cn(
                  "pointer-events-none absolute top-0 w-full px-8 text-muted-foreground",
                  placeholderClassName
                )}
              >
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
