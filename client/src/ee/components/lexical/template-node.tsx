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
    variable: string;
    value: any;
    isError: boolean;
  },
  SerializedTextNode
>;

const formatTemplateValue = (value: any): string => {
  if (value === null || value === undefined || value === "")
    return "[No Value]";

  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch (e) {
      return "[Object]";
    }
  }

  return String(value);
};

function $convertTemplateElement(
  domNode: HTMLElement
): DOMConversionOutput | null {
  const textContent = domNode.textContent;
  const isError = domNode.getAttribute("data-error") === "true";

  if (textContent !== null) {
    const node = $createTemplateNode(textContent, null, isError);
    return {
      node,
    };
  }

  return null;
}

export class TemplateNode extends TextNode {
  __variable: string;
  __value: any;
  __isError: boolean;
  __showingVariable: boolean;

  static getType(): string {
    return "template-node";
  }

  static clone(node: TemplateNode): TemplateNode {
    return new TemplateNode(
      node.__variable,
      node.__value,
      node.__isError,
      node.__showingVariable,
      node.__text,
      node.__key
    );
  }

  static importJSON(serializedNode: SerializedTemplateNode): TemplateNode {
    const node = $createTemplateNode(
      serializedNode.variable,
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
    variable: string,
    value: any,
    isError: boolean = false,
    showVariable: boolean = true,
    text?: string,
    key?: NodeKey
  ) {
    super(text ?? variable, key);
    this.__variable = variable;
    this.__value = value;
    this.__isError = isError;
    this.__showingVariable = showVariable;
  }

  exportJSON(): SerializedTemplateNode {
    return {
      ...super.exportJSON(),
      variable: this.__variable,
      value: this.__value,
      isError: this.__isError,
      type: "template-node",
      version: 1,
    };
  }

  createDOM(config: EditorConfig): HTMLElement {
    const dom = super.createDOM(config);
    if (this.__showingVariable) {
      // Show the variable as plain text
      dom.textContent = `${this.__variable}`;
      dom.className = this.__isError
        ? "text-red-500 font-normal"
        : "text-mirascope font-normal cursor-pointer";
    } else {
      dom.textContent = formatTemplateValue(this.__value);
      if (dom.textContent !== "[No Value]") {
        dom.className = "text-primary font-normal cursor-pointer";
      } else {
        dom.className = "text-gray-500/70 font-italic cursor-pointer";
      }
    }
    dom.setAttribute("data-lexical-template", "true");
    dom.setAttribute("data-error", this.__isError.toString());

    return dom;
  }

  updateDOM(
    _prevNode: TextNode,
    dom: HTMLElement,
    _config: EditorConfig
  ): boolean {
    if (this.__showingVariable) {
      dom.textContent = `${this.__variable}`;
      dom.className = this.__isError
        ? "text-red-500 font-normal"
        : "text-mirascope font-normal cursor-pointer";
    } else {
      dom.textContent = formatTemplateValue(this.__value);
      if (dom.textContent !== "[No Value]") {
        dom.className = "text-primary font-normal cursor-pointer";
      } else {
        dom.className = "text-gray-500/70 font-italic cursor-pointer";
      }
    }

    dom.setAttribute("data-lexical-template", "true");
    dom.setAttribute("data-error", this.__isError.toString());

    return false;
  }

  exportDOM(): DOMExportOutput {
    const element = document.createElement("span");
    element.setAttribute("data-lexical-template", "true");
    element.setAttribute("data-error", this.__isError.toString());
    element.textContent = this.__variable;

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
    // This always needs to return the variable name for getting the prompt template
    return this.__variable;
  }

  isTextEntity(): true {
    return true;
  }

  setShowingVariable(showingVariable: boolean): this {
    const self = this.getWritable();
    self.__showingVariable = showingVariable;
    return self;
  }

  setVariableValue(value: any): this {
    const self = this.getWritable();
    self.__value = value;
    return self;
  }

  getVariableValue(): any {
    return this.__value;
  }

  getShowingVariable(): boolean {
    return this.__showingVariable;
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
  variable: string,
  value: any,
  isError: boolean = false,
  showVariable: boolean = true
): TemplateNode {
  const templateNode = new TemplateNode(variable, value, isError, showVariable);
  return $applyNodeReplacement(
    templateNode.setMode("normal").toggleDirectionless()
  );
}

export function $isTemplateNode(
  node: LexicalNode | null | undefined
): node is TemplateNode {
  return node instanceof TemplateNode;
}

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
