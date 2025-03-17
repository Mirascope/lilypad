import { EditorParameters } from "@/ee/components/Playground";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { mergeRegister } from "@lexical/utils";
import {
  $getNearestNodeFromDOMNode,
  $getSelection,
  COMMAND_PRIORITY_LOW,
  createCommand,
  DELETE_CHARACTER_COMMAND,
  getNearestEditorFromDOMNode,
  LexicalCommand,
  LexicalEditor,
  TextNode,
} from "lexical";
import { JSX, useCallback, useEffect } from "react";
import {
  useFieldArray,
  UseFieldArrayAppend,
  useFormContext,
} from "react-hook-form";
import {
  $createTemplateNode,
  $isTemplateNode,
  TemplateNode,
} from "./template-node";

export const TOGGLE_SHOW_VARIABLE_COMMAND: LexicalCommand<boolean> =
  createCommand();

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
  const isValid =
    inputs.includes(parsed.variable) &&
    (parsed.format === undefined ||
      validFormats.includes(parsed.format) ||
      pythonFormatterPattern.test(parsed.format));

  return { isValid, parsed };
};

const findAndTransformTemplate = (
  editor: LexicalEditor,
  node: TextNode,
  inputs: readonly string[],
  inputValues: Record<string, any>,
  append: UseFieldArrayAppend<
    EditorParameters,
    "inputs" | `inputs.${number}.${string}`
  >
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
    const value = inputValues[parsed.variable];
    const templateNode = $createTemplateNode(matchedText, value, !isValid);
    targetNode.replace(templateNode);
    if (value === undefined) {
      append({ key: parsed.variable, type: "str", value: "" });
    }
    editor.focus();
    return templateNode;
  }

  return null;
};

const updateTemplateNode = (
  node: TemplateNode,
  inputs: readonly string[],
  inputValues: Record<string, any>
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
  const value = inputValues[parsed.variable];
  if (node.getVariableValue() !== value) {
    node.setVariableValue(value);
  }
  if (node.isError() !== !isValid) {
    const updated = $createTemplateNode(text, value, !isValid, true);
    node.replace(updated);
  }
};

const useTemplates = (
  editor: LexicalEditor,
  inputs: readonly string[],
  inputValues: Record<string, any>
): void => {
  const methods = useFormContext<EditorParameters>();
  const { fields, append, remove } = useFieldArray<EditorParameters>({
    control: methods.control,
    name: "inputs",
  });
  // Transform function for regular text nodes
  const textTransformFunction = useCallback(
    (node: TextNode) => {
      if (!$isTemplateNode(node)) {
        let targetNode: TextNode | null = node;
        while (targetNode !== null) {
          if (!targetNode.isSimpleText()) {
            return;
          }
          targetNode = findAndTransformTemplate(
            editor,
            targetNode,
            inputs,
            inputValues,
            append
          );
        }
      }
    },
    [inputs, inputValues]
  );

  // Transform function for template nodes
  const templateTransformFunction = useCallback(
    (node: TemplateNode) => {
      updateTemplateNode(node, inputs, inputValues);
    },
    [inputs, inputValues]
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

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      const target = event.target;
      if (!isDOMNode(target)) {
        return;
      }
      const nearestEditor = getNearestEditorFromDOMNode(target);
      if (nearestEditor === null) {
        return;
      }

      nearestEditor.update(() => {
        const clickedNode = $getNearestNodeFromDOMNode(target);
        if (clickedNode !== null) {
          if ($isTemplateNode(clickedNode)) {
            clickedNode.setShowingVariable(!clickedNode.getShowingVariable());
          }
        }
      });

      event.preventDefault();
    };

    const onMouseUp = (event: MouseEvent) => {
      if (event.button === 1) {
        onClick(event);
      }
    };

    return editor.registerRootListener((rootElement, prevRootElement) => {
      if (prevRootElement !== null) {
        prevRootElement.removeEventListener("click", onClick);
        prevRootElement.removeEventListener("mouseup", onMouseUp);
      }
      if (rootElement !== null) {
        rootElement.addEventListener("click", onClick);
        rootElement.addEventListener("mouseup", onMouseUp);
      }
    });
  }, [editor]);
};

export const TemplatePlugin = ({
  inputs,
  inputValues,
}: {
  inputs: readonly string[];
  inputValues: Record<string, any>;
}): JSX.Element | null => {
  const [editor] = useLexicalComposerContext();
  useEffect(() => {
    if (!editor.hasNodes([TemplateNode])) {
      throw new Error(
        "TemplateAutoReplacePlugin: TemplateNode not registered on editor"
      );
    }
  }, [editor]);

  useEffect(() => {
    return editor.registerCommand(
      TOGGLE_SHOW_VARIABLE_COMMAND,
      (payload) => {
        editor.update(() => {
          // Find all template nodes and update their showingVariable state
          const nodes = editor.getEditorState()._nodeMap;
          for (const [, node] of nodes) {
            if ($isTemplateNode(node)) {
              if (payload !== undefined) {
                node.setShowingVariable(payload);
              } else {
                node.setShowingVariable(!node.getShowingVariable());
              }
            }
          }
        });
        return true;
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor]);

  const onBackspaceCommand = useCallback(() => {
    const selection = $getSelection();
    if (selection === null) {
      return false;
    }
    const nodes = selection.getNodes();
    const node = nodes[0];

    // Prevent custom dedcorator node deletion with backspace command
    if ($isTemplateNode(node) && !node.__showingVariable) {
      return true;
    }

    return false;
  }, []);

  useEffect(() => {
    return mergeRegister(
      editor.registerCommand(
        DELETE_CHARACTER_COMMAND,
        onBackspaceCommand,
        COMMAND_PRIORITY_LOW
      )
    );
  }, []);

  useTemplates(editor, inputs, inputValues);
  return null;
};

function isDOMNode(x: unknown): x is Node {
  return (
    typeof x === "object" &&
    x !== null &&
    "nodeType" in x &&
    typeof x.nodeType === "number"
  );
}
