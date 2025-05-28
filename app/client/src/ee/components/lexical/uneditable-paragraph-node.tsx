import {
  $applyNodeReplacement,
  EditorConfig,
  LexicalNode,
  ParagraphNode,
  SerializedParagraphNode,
} from "lexical";

export type SerializedUneditableParagraphNode = SerializedParagraphNode;

export class UneditableParagraphNode extends ParagraphNode {
  static getType(): string {
    return "uneditable-paragraph";
  }

  static clone(node: UneditableParagraphNode): UneditableParagraphNode {
    return new UneditableParagraphNode(node.__key);
  }

  createDOM(config: EditorConfig): HTMLElement {
    const dom = super.createDOM(config);
    dom.setAttribute("data-lexical-uneditable", "true");
    dom.contentEditable = "false";
    return dom;
  }

  updateDOM(_prevNode: UneditableParagraphNode, _dom: HTMLElement): boolean {
    return false;
  }

  static importJSON(serializedNode: SerializedUneditableParagraphNode): UneditableParagraphNode {
    const node = $createUneditableParagraphNode();
    node.setFormat(serializedNode.format);
    node.setIndent(serializedNode.indent);
    node.setDirection(serializedNode.direction);
    return node;
  }

  exportJSON(): SerializedUneditableParagraphNode {
    return {
      ...super.exportJSON(),
      type: this.getType(),
      version: 1,
    };
  }

  isEditable(): boolean {
    return false;
  }
}

export function $createUneditableParagraphNode(): UneditableParagraphNode {
  return $applyNodeReplacement(new UneditableParagraphNode());
}

export function $isUneditableParagraphNode(
  node: LexicalNode | null | undefined
): node is UneditableParagraphNode {
  return node instanceof UneditableParagraphNode;
}
