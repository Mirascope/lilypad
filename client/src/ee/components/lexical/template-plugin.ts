import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { LexicalEditor, TextNode } from "lexical";
import { JSX, useCallback, useEffect } from "react";
import {
  $createTemplateNode,
  $isTemplateNode,
  TemplateNode,
} from "./template-node";

const parseTemplate = (
  template: string
): {
  variable: string;
  format?: string;
  fullMatch: string;
} | null => {
  // Check for single pair of braces
  const braceCount = (template.match(/\{/g) || []).length;
  if (braceCount !== 1) return null;

  const regex = /^\{([^:}]+)(?::([^}]+))?\}$/;
  const match = template.match(regex);

  if (!match) {
    return null;
  }

  return {
    variable: match[1],
    format: match[2],
    fullMatch: match[0],
  };
};

const checkTemplateValidity = (
  text: string,
  inputs: readonly string[]
): { isValid: boolean; parsed: ReturnType<typeof parseTemplate> } => {
  const parsed = parseTemplate(text);

  if (!parsed) {
    return { isValid: false, parsed: null };
  }

  const validFormats = [
    "list",
    "lists",
    "image",
    "images",
    "audio",
    "audios",
    "text",
    "texts",
  ];
  const pythonFormatterPattern = /^[,.0-9+\-#% ]*[defgxobcnEFGXOBCN%]?$/;
  // const isValid =
  //   inputs.includes(parsed.variable) &&
  //   (parsed.format === undefined ||
  //     validFormats.includes(parsed.format) ||
  //     pythonFormatterPattern.test(parsed.format));
  const isValid = true;

  return { isValid, parsed };
};

const findAndTransformTemplate = (
  node: TextNode,
  inputs: readonly string[]
): null | TextNode => {
  const text = node.getTextContent();
  const regex = /\{[^{}]*\}/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    const matchedText = match[0];

    // Count braces in the entire text before this match
    const textBeforeMatch = text.slice(0, match.index);
    const openBracesBeforeMatch = (textBeforeMatch.match(/\{/g) || []).length;
    const closeBracesBeforeMatch = (textBeforeMatch.match(/\}/g) || []).length;

    // Skip if we're inside another brace pair
    if (openBracesBeforeMatch !== closeBracesBeforeMatch) {
      continue;
    }

    const { isValid, parsed } = checkTemplateValidity(matchedText, inputs);

    // Skip invalid template syntax
    if (!parsed) {
      continue;
    }

    const startOffset = match.index;
    const endOffset = startOffset + matchedText.length;

    let targetNode;
    if (startOffset === 0) {
      [targetNode] = node.splitText(endOffset);
    } else {
      [, targetNode] = node.splitText(startOffset, endOffset);
    }

    const templateNode = $createTemplateNode(matchedText, !isValid);
    targetNode.replace(templateNode);
    return templateNode;
  }

  return null;
};

const updateTemplateNode = (
  node: TemplateNode,
  inputs: readonly string[]
): void => {
  const text = node.getTextContent();
  const { isValid, parsed } = checkTemplateValidity(text, inputs);

  // If the template syntax itself is invalid (like multiple braces),
  // convert back to regular text
  if (!parsed) {
    const textNode = new TextNode(text);
    node.replace(textNode);
    return;
  }

  // Otherwise update the error state if needed
  if (node.isError() !== !isValid) {
    const updated = $createTemplateNode(text, !isValid);
    node.replace(updated);
  }
};

const useTemplates = (
  editor: LexicalEditor,
  inputs: readonly string[]
): void => {
  // Transform function for regular text nodes
  const textTransformFunction = useCallback(
    (node: TextNode) => {
      if (!$isTemplateNode(node)) {
        let targetNode: TextNode | null = node;
        while (targetNode !== null) {
          if (!targetNode.isSimpleText()) {
            return;
          }
          targetNode = findAndTransformTemplate(targetNode, inputs);
        }
      }
    },
    [inputs]
  );

  // Transform function for template nodes
  const templateTransformFunction = useCallback(
    (node: TemplateNode) => {
      updateTemplateNode(node, inputs);
    },
    [inputs]
  );

  useEffect(() => {
    editor.setEditable(false);

    if (!editor.hasNodes([TemplateNode])) {
      throw new Error(
        "TemplateAutoReplacePlugin: TemplateNode not registered on editor"
      );
    }
    const removeTextTransform = editor.registerNodeTransform(
      TextNode,
      textTransformFunction
    );

    const removeTemplateTransform = editor.registerNodeTransform(
      TemplateNode,
      templateTransformFunction
    );
    requestAnimationFrame(() => editor.setEditable(true));
    return () => {
      removeTextTransform();
      removeTemplateTransform();
    };
  }, [editor, textTransformFunction, templateTransformFunction]);
};

export const TemplatePlugin = ({
  inputs,
}: {
  inputs: readonly string[];
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
