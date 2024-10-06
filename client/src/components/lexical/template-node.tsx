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

// Define the type for the serialized template node
export type SerializedTemplateNode = Spread<
  {
    value: string;
    moreDetails?: object;
  },
  SerializedTextNode
>;

// Function to convert a DOM element to a template node
function $convertTemplateElement(
  domNode: HTMLElement
): DOMConversionOutput | null {
  const textContent = domNode.textContent;

  if (textContent !== null) {
    const node = $createTemplateNode(textContent);
    return {
      node,
    };
  }

  return null;
}

export class TemplateNode extends TextNode {
  __value: string;
  __moreDetails?: object;

  // Return the type of the node
  static getType(): string {
    return "template-node";
  }

  // Clone the node
  static clone(node: TemplateNode): TemplateNode {
    return new TemplateNode(
      node.__value,
      node.__moreDetails,
      node.__text,
      node.__key
    );
  }

  // Import the serialized node
  static importJSON(serializedNode: SerializedTemplateNode): TemplateNode {
    const node = $createTemplateNode(
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
  exportJSON(): SerializedTemplateNode {
    return {
      ...super.exportJSON(),
      value: this.__value,
      moreDetails: this.__moreDetails,
      type: "template-node",
      version: 1,
    };
  }

  // Create the DOM representation of the node
  createDOM(config: EditorConfig): HTMLElement {
    const dom = super.createDOM(config);
    dom.textContent = this.__value;
    dom.setAttribute("data-lexical-template", "true");
    dom.className = "text-purple-500 font-normal ";
    return dom;
  }

  // Export the DOM representation of the node
  exportDOM(): DOMExportOutput {
    const element = document.createElement("span");
    element.setAttribute("data-lexical-template", "true");
    element.textContent = this.__text;
    return { element };
  }

  // Import the DOM conversion map for the node
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

// Helper function to create a new template node
export function $createTemplateNode(
  value: string,
  moreDetails?: object
): TemplateNode {
  const templateNode = new TemplateNode(value, moreDetails);
  templateNode.setMode("segmented").toggleDirectionless();
  return $applyNodeReplacement(templateNode);
}

// Helper function to check if a node is a template node
export function $isTemplateNode(
  node: LexicalNode | null | undefined
): node is TemplateNode {
  return node instanceof TemplateNode;
}
