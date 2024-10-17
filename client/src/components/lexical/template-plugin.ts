import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { LexicalEditor, TextNode } from "lexical";
import { useEffect } from "react";
import { $createTemplateNode, TemplateNode } from "./template-node";

function $findAndTransformTemplate(
  node: TextNode,
  inputs: string[]
): null | TextNode {
  const text = node.getTextContent();
  const regex = /\{(.*?)\}/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    const matchedContent = match[1]; // Content inside the braces
    const startOffset = match.index;
    const endOffset = startOffset + match[0].length; // Include braces in length
    let targetNode;
    if (startOffset === 0) {
      [targetNode] = node.splitText(endOffset);
    } else {
      [, targetNode] = node.splitText(startOffset, endOffset);
    }
    const isError = !inputs.includes(matchedContent);
    const templateNode = $createTemplateNode(match[0], isError);
    targetNode.replace(templateNode);
    return templateNode;
  }
  return null;
}

function $textNodeTransform(node: TextNode, inputs: string[]): void {
  let targetNode: TextNode | null = node;

  while (targetNode !== null) {
    if (!targetNode.isSimpleText()) {
      return;
    }
    targetNode = $findAndTransformTemplate(targetNode, inputs);
  }
}

function useTemplates(editor: LexicalEditor, inputs: string[]): void {
  useEffect(() => {
    if (!editor.hasNodes([TemplateNode])) {
      throw new Error(
        "TemplateAutoReplacePlugin: TemplateNode not registered on editor"
      );
    }

    return editor.registerNodeTransform(TextNode, (node: TextNode) => {
      $textNodeTransform(node, inputs);
    });
  }, [editor, inputs]);
}

export const TemplatePlugin = ({
  inputs,
}: {
  inputs: string[];
}): JSX.Element | null => {
  const [editor] = useLexicalComposerContext();
  useEffect(() => {
    if (!editor.hasNodes([TemplateNode])) {
      throw new Error(
        "TemplateAutoReplacePlugin: TemplateNode not registered on editor"
      );
    }
  }, [editor]);
  useTemplates(editor, inputs);
  return null;
};
