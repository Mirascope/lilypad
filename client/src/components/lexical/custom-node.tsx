import {
  $applyNodeReplacement,
  type DOMConversionMap,
  type DOMConversionOutput,
  type DOMExportOutput,
  type EditorConfig,
  type LexicalNode,
  type NodeKey,
  type SerializedTextNode,
  type Spread,
  TextNode,
} from "lexical";

// Define the type for the serialized custom node
export type SerializedCustomNode = Spread<
  {
    value: string;
    moreDetails?: object;
  },
  SerializedTextNode
>;

// Function to convert a DOM element to a custom node
function $convertCustomElement(
  domNode: HTMLElement
): DOMConversionOutput | null {
  const textContent = domNode.textContent;

  if (textContent !== null) {
    const node = $createCustomNode(textContent);
    return {
      node,
    };
  }

  return null;
}

export class CustomNode extends TextNode {
  __value: string;
  __moreDetails?: object;

  // Return the type of the node
  static getType(): string {
    return "custom-node";
  }

  // Clone the node
  static clone(node: CustomNode): CustomNode {
    return new CustomNode(
      node.__value,
      node.__moreDetails,
      node.__text,
      node.__key
    );
  }

  // Import the serialized node
  static importJSON(serializedNode: SerializedCustomNode): CustomNode {
    const node = $createCustomNode(
      serializedNode.value,
      serializedNode.moreDetails
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
    moreDetails?: object,
    text?: string,
    key?: NodeKey
  ) {
    super(text ?? value, key);
    this.__value = value;
    this.__moreDetails = moreDetails;
  }

  // Export the node to a serialized format
  exportJSON(): SerializedCustomNode {
    return {
      ...super.exportJSON(),
      value: this.__value,
      moreDetails: this.__moreDetails,
      type: "custom-node",
      version: 1,
    };
  }

  // Create the DOM representation of the node
  createDOM(config: EditorConfig): HTMLElement {
    const dom = super.createDOM(config);
    dom.textContent = this.__value;
    dom.className = "text-purple-500 font-normal ";
    return dom;
  }

  // Export the DOM representation of the node
  exportDOM(): DOMExportOutput {
    const element = document.createElement("span");
    element.setAttribute("data-lexical-custom", "true");
    element.textContent = this.__text;
    return { element };
  }

  // Import the DOM conversion map for the node
  static importDOM(): DOMConversionMap | null {
    return {
      span: (domNode: HTMLElement) => {
        if (!domNode.hasAttribute("data-lexical-custom")) {
          return null;
        }
        return {
          conversion: $convertCustomElement,
          priority: 1,
        };
      },
    };
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
}

// Helper function to create a new custom node
export function $createCustomNode(
  value: string,
  moreDetails?: object
): CustomNode {
  const customNode = new CustomNode(value, moreDetails);
  customNode.setMode("segmented").toggleDirectionless();
  return $applyNodeReplacement(customNode);
}

// Helper function to check if a node is a custom node
export function $isCustomNode(
  node: LexicalNode | null | undefined
): node is CustomNode {
  return node instanceof CustomNode;
}
