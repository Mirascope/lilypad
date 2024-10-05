import type { ElementTransformer, Transformer } from "@lexical/markdown";
import type { ElementNode, LexicalNode } from "lexical";

import {
  $convertToMarkdownString,
  ELEMENT_TRANSFORMERS,
  TEXT_FORMAT_TRANSFORMERS,
  TEXT_MATCH_TRANSFORMERS,
  TRANSFORMERS,
} from "@lexical/markdown";
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
import { UneditableParagraphNode } from "./uneditable-paragraph-node";
import {
  $isCollapsibleTitleNode,
  CollapsibleTitleNode,
} from "./collapsible-title-node";
import {
  $isCollapsibleContentNode,
  CollapsibleContentNode,
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
export const COLLAPSIBLE_TRANSFORMER: ElementTransformer = {
  dependencies: [CollapsibleContainerNode],
  type: "element",

  // Export function for code blocks
  export: (node, traverseChildren) => {
    if ($isCollapsibleContainerNode(node)) {
      const titleNode = node.getFirstChild();
      const contentNode = node.getLastChild();
      let titleMarkdown = "";
      let contentMarkdown = "";

      if ($isCollapsibleTitleNode(titleNode)) {
        titleMarkdown = traverseChildren(titleNode).trim();
      }

      if ($isCollapsibleContentNode(contentNode)) {
        contentMarkdown = $convertToMarkdownString(TRANSFORMERS, contentNode);
      }

      // Combine the title and content markdown with desired formatting
      // Ensure that there are appropriate newlines
      return `${titleMarkdown}:\n${contentMarkdown}`;
    }
    return null;
  },

  // RegExp to match code blocks in markdown
  regExp: /^([A-Z]*):$/gm,

  // Replace function to convert markdown code blocks back to Lexical nodes
  replace: (parentNode, _1, _2, isImport) => {
    const containerNode = $createCollapsibleContainerNode(true);
    if (isImport || parentNode.getNextSibling() != null) {
      parentNode.replace(containerNode);
    } else {
      parentNode.insertBefore(containerNode);
    }

    containerNode.selectNext();
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
  COLLAPSIBLE_TRANSFORMER,
  ...TRANSFORMERS,
];
