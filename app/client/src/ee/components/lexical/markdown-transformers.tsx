import type {
  ElementTransformer,
  MultilineElementTransformer,
  Transformer,
} from "@lexical/markdown";
import { $createParagraphNode, $createTextNode, type LexicalNode } from "lexical";

import { TRANSFORMERS } from "@lexical/markdown";
import {
  $createHorizontalRuleNode,
  $isHorizontalRuleNode,
  HorizontalRuleNode,
} from "@lexical/react/LexicalHorizontalRuleNode";
import {
  $createCollapsibleContainerNode,
  $isCollapsibleContainerNode,
  CollapsibleContainerNode,
} from "./collapsible-container-node";
import { $createUneditableParagraphNode } from "./uneditable-paragraph-node";
import {
  $createCollapsibleTitleNode,
  $isCollapsibleTitleNode,
  CollapsibleTitleNode,
} from "./collapsible-title-node";
import {
  $createCollapsibleContentNode,
  $isCollapsibleContentNode,
} from "./collapsible-content-node";
import { $createCodeNode, $isCodeNode, CodeNode } from "@lexical/code";

export const CODE_BLOCK_TRANSFORMER: ElementTransformer = {
  dependencies: [CodeNode],
  type: "element",

  // Export function for code blocks
  export: (node) => {
    if ($isCodeNode(node)) {
      const language = node.getLanguage() || "";
      const codeContent = node.getTextContent();
      return `\`\`\`${language}\n${codeContent}\n\`\`\``;
    }
    return null;
  },

  // RegExp to match code blocks in markdown
  regExp: /^```([a-z]*)\n([\s\S]*?)\n```$/gm,

  // Replace function to convert markdown code blocks back to Lexical nodes
  replace: (parentNode, _1, _2, isImport) => {
    const codeNode = $createCodeNode();
    if (isImport || parentNode.getNextSibling() != null) {
      parentNode.replace(codeNode);
    } else {
      parentNode.insertBefore(codeNode);
    }

    codeNode.selectNext();
  },
};

const trimEmptyStrings = (arr: string[]): string[] => {
  const result: string[] = [];
  let lastContentIndex = -1;

  for (let i = 0; i < arr.length; i++) {
    if (arr[i] !== "" || (lastContentIndex !== -1 && arr.slice(i).some((item) => item !== ""))) {
      result.push(arr[i]);
      if (arr[i] !== "") {
        lastContentIndex = result.length - 1;
      }
    }
  }

  return result;
};
export const COLLAPSIBLE_TRANSFORMER: MultilineElementTransformer = {
  dependencies: [CollapsibleContainerNode],
  type: "multiline-element",

  // Export function for code blocks
  export: (node, traverseChildren) => {
    if ($isCollapsibleContainerNode(node)) {
      const titleNode = node.getFirstChild<CollapsibleTitleNode>();
      const contentNode = node.getLastChild<CollapsibleContainerNode>();
      let titleMarkdown = "";
      let contentMarkdown = "";

      if ($isCollapsibleTitleNode(titleNode)) {
        titleMarkdown = traverseChildren(titleNode).trim();
        if (titleMarkdown.endsWith(":")) {
          titleMarkdown = titleMarkdown.slice(0, -1);
        }
      }

      if ($isCollapsibleContentNode(contentNode)) {
        const contentChildren = contentNode.getChildren();
        for (const child of contentChildren) {
          contentMarkdown += `${child.getTextContent()}\n`;
        }
      }

      // Combine the title and content markdown with desired formatting
      // Ensure that there are appropriate newlines
      return `${titleMarkdown}:\n${contentMarkdown}`;
    }
    return null;
  },

  // RegExp to match code blocks in markdown
  regExpStart: /^([A-Z]*):$/gm,
  regExpEnd: {
    regExp: /^(\s*$)/m,
    optional: true,
  },

  // Replace function to convert markdown code blocks back to Lexical nodes
  replace: (rootNode, _children, startMatch, _endMatch, linesInBetween, isImport) => {
    if (!isImport) return true;
    const containerNode = $createCollapsibleContainerNode(true);
    // create title node
    const titleNode = $createCollapsibleTitleNode().append(
      $createUneditableParagraphNode().append($createTextNode(startMatch[0]))
    );
    const contentNode = $createCollapsibleContentNode();
    // TODO: Look into why linesInBetween has many empty strings not in the original markdown
    // Remove empty lines from the start and end, keep the ones in between
    if (linesInBetween) {
      linesInBetween = trimEmptyStrings(linesInBetween);
    }
    for (const line of linesInBetween || []) {
      contentNode.append($createParagraphNode().append($createTextNode(line)));
    }
    containerNode.append(titleNode, contentNode);
    rootNode.append(containerNode);
  },
};
export const HR: ElementTransformer = {
  dependencies: [HorizontalRuleNode],
  export: (node: LexicalNode) => {
    return $isHorizontalRuleNode(node) ? "***" : null;
  },
  regExp: /^(---|\*\*\*|___)\s?$/,
  replace: (parentNode, _1, _2, isImport) => {
    const line = $createHorizontalRuleNode();

    if (isImport || parentNode.getNextSibling() != null) {
      parentNode.replace(line);
    } else {
      parentNode.insertBefore(line);
    }

    line.selectNext();
  },
  type: "element",
};

export const PLAYGROUND_TRANSFORMERS: Array<Transformer> = [
  HR,
  CODE_BLOCK_TRANSFORMER,
  ...TRANSFORMERS,
  COLLAPSIBLE_TRANSFORMER,
];
