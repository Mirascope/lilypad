import { TextNode } from "lexical";
import { $createCustomNode, CustomNode } from "./custom-node";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { useEffect, useCallback, useMemo } from "react";
import { useLexicalTextEntity } from "@lexical/react/useLexicalTextEntity";

const escapeRegExp = (string: string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
};

export const TemplateAutoReplacePlugin = ({
  inputs,
}: {
  inputs: string[];
}): JSX.Element | null => {
  const [editor] = useLexicalComposerContext();
  useEffect(() => {
    if (!editor.hasNodes([CustomNode])) {
      throw new Error(
        "TemplateAutoReplacePlugin: CustomNode not registered on editor"
      );
    }
  }, [editor]);

  const $createCustomNode_ = useCallback((textNode: TextNode): CustomNode => {
    return $createCustomNode(textNode.getTextContent());
  }, []);

  const contentPattern = inputs.map(escapeRegExp).join("|");

  const getTemplateMatch = useCallback((text: string) => {
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
  }, []);

  // useLexicalTextEntity<CustomNode>(
  //   getTemplateMatch,
  //   CustomNode,
  //   $createCustomNode_
  // );

  return null;
};
