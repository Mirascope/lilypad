import { TextNode } from "lexical";
import { $createTemplateNode, TemplateNode } from "./template-node";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { useEffect, useCallback } from "react";
import { useLexicalTextEntity } from "@lexical/react/useLexicalTextEntity";

const escapeRegExp = (string: string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
};

export const TemplateAutoReplacePlugin = (
  {
    // inputs,
  }: {
    // inputs: string[];
  }
): JSX.Element | null => {
  const [editor] = useLexicalComposerContext();
  const inputs: string[] = ["genre"];
  useEffect(() => {
    if (!editor.hasNodes([TemplateNode])) {
      throw new Error(
        "TemplateAutoReplacePlugin: TemplateNode not registered on editor"
      );
    }
  }, [editor]);

  const createTemplateNode = useCallback((textNode: TextNode): TemplateNode => {
    return $createTemplateNode(textNode.getTextContent());
  }, []);
  console.log(inputs);
  const getTemplateMatch = useCallback(
    (text: string) => {
      console.log(inputs);
      const contentPattern = inputs.map(escapeRegExp).join("|");
      const matchArr = new RegExp(
        `(?<!\\{)\\{(${contentPattern})\\}(?!\\})`,
        "g"
      ).exec(text);

      if (matchArr === null) {
        return null;
      }

      const matchedContent = matchArr[1];
      const startOffset = matchArr.index;
      const endOffset = startOffset + matchedContent.length + 2; // +2 for the braces
      return {
        end: endOffset,
        start: startOffset,
      };
    },
    [JSON.stringify(inputs)]
  );

  useLexicalTextEntity<TemplateNode>(
    getTemplateMatch,
    TemplateNode,
    createTemplateNode
  );

  return null;
};
