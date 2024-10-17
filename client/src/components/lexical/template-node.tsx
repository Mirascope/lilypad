import {
  $applyNodeReplacement,
  type DOMConversionMap,
  type DOMConversionOutput,
  type DOMExportOutput,
  type EditorConfig,
  LexicalEditor,
  type LexicalNode,
  type NodeKey,
  type SerializedTextNode,
  type Spread,
  TextNode,
} from "lexical";

export type SerializedTemplateNode = Spread<
  {
    value: string;
    isError: boolean;
  },
  SerializedTextNode
>;

function $convertTemplateElement(
  domNode: HTMLElement
): DOMConversionOutput | null {
  const textContent = domNode.textContent;
  const isError = domNode.getAttribute("data-error") === "true";

  if (textContent !== null) {
    const node = $createTemplateNode(textContent, undefined, isError);
    return {
      node,
    };
  }

  return null;
}

export class TemplateNode extends TextNode {
  __value: string;
  __isError: boolean;

  static getType(): string {
    return "template-node";
  }

  static clone(node: TemplateNode): TemplateNode {
    return new TemplateNode(
      node.__value,
      node.__isError,
      node.__text,
      node.__key
    );
  }

  static importJSON(serializedNode: SerializedTemplateNode): TemplateNode {
    const node = $createTemplateNode(
      serializedNode.value,
      serializedNode.isError
    );
    node.setTextContent(serializedNode.text);
    node.setFormat(serializedNode.format);
    node.setDetail(serializedNode.detail);
    node.setMode(serializedNode.mode);
    node.setStyle(serializedNode.style);
    return node;
  }

  constructor(
    value: string,
    isError: boolean = false,
    text?: string,
    key?: NodeKey
  ) {
    super(text ?? value, key);
    this.__value = value;
    this.__isError = isError;
  }

  exportJSON(): SerializedTemplateNode {
    return {
      ...super.exportJSON(),
      value: this.__value,
      isError: this.__isError,
      type: "template-node",
      version: 1,
    };
  }

  createDOM(config: EditorConfig): HTMLElement {
    const dom = super.createDOM(config);
    dom.textContent = this.__value;
    dom.setAttribute("data-lexical-template", "true");
    dom.setAttribute("data-error", this.__isError.toString());
    dom.className = this.__isError
      ? "text-red-500 font-normal"
      : "text-purple-500 font-normal";
    return dom;
  }

  exportDOM(): DOMExportOutput {
    const element = document.createElement("span");
    element.setAttribute("data-lexical-template", "true");
    element.setAttribute("data-error", this.__isError.toString());
    element.textContent = this.__text;
    return { element };
  }

  static importDOM(): DOMConversionMap | null {
    return {
      span: (domNode: HTMLElement) => {
        if (!domNode.hasAttribute("data-lexical-template")) {
          return null;
        }
        return {
          conversion: $convertTemplateElement,
          priority: 1,
        };
      },
    };
  }

  getValue(): string {
    return this.__value;
  }
  isTextEntity(): true {
    return true;
  }

  canInsertTextBefore(): boolean {
    return false;
  }

  canInsertTextAfter(): boolean {
    return false;
  }

  isError(): boolean {
    return this.__isError;
  }
}

export function $createTemplateNode(
  value: string,
  isError: boolean = false
): TemplateNode {
  const templateNode = new TemplateNode(value, isError);
  templateNode.setMode("segmented").toggleDirectionless();
  return $applyNodeReplacement(templateNode);
}

export function $isTemplateNode(
  node: LexicalNode | null | undefined
): node is TemplateNode {
  return node instanceof TemplateNode;
}

// New function to find error template nodes
export function $findErrorTemplateNodes(editor: LexicalEditor): TemplateNode[] {
  const errorNodes: TemplateNode[] = [];
  editor.getEditorState().read(() => {
    const nodes = editor.getEditorState()._nodeMap;
    for (const [, node] of nodes) {
      if ($isTemplateNode(node) && node.isError()) {
        errorNodes.push(node);
      }
    }
  });
  return errorNodes;
}
