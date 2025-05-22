import { $createParagraphNode, $getSelection } from "lexical";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { $createCodeNode } from "@lexical/code";
import {
  INSERT_ORDERED_LIST_COMMAND,
  INSERT_UNORDERED_LIST_COMMAND,
  REMOVE_LIST_COMMAND,
} from "@lexical/list";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { $createHeadingNode, $createQuoteNode, HeadingTagType } from "@lexical/rich-text";
import { $setBlocksType } from "@lexical/selection";
import { INSERT_COLLAPSIBLE_COMMAND } from "./collapsible-plugin";

export const blockTypeToBlockName: Record<string, string> = {
  h1: "Heading 1",
  h2: "Heading 2",
  h3: "Heading 3",
  h4: "Heading 4",
  h5: "Heading 5",
  h6: "Heading 6",
  paragraph: "Normal",
  quote: "Quote",
  bullet: "Bulleted List",
  number: "Numbered List",
  code: "Code Block",
};

interface BlockTypeDropdownProps {
  blockType: keyof typeof blockTypeToBlockName;
  isEditable: boolean;
  isLLM?: boolean;
}

export const BlockTypeDropdown = ({
  blockType,
  isEditable,
  isLLM = false,
}: BlockTypeDropdownProps) => {
  const [editor] = useLexicalComposerContext();

  const formatHeading = (headingLevel: HeadingTagType) => {
    editor.update(() => {
      const selection = $getSelection();
      $setBlocksType(selection, () => $createHeadingNode(headingLevel));
    });
  };

  const formatParagraph = () => {
    editor.update(() => {
      const selection = $getSelection();
      $setBlocksType(selection, () => $createParagraphNode());
    });
  };

  const formatOrderedList = () => {
    if (blockType !== "number") {
      editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);
    } else {
      editor.dispatchCommand(REMOVE_LIST_COMMAND, undefined);
    }
  };

  const formatUnorderedList = () => {
    if (blockType !== "bullet") {
      editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
    } else {
      editor.dispatchCommand(REMOVE_LIST_COMMAND, undefined);
    }
  };

  const formatQuote = () => {
    editor.update(() => {
      const selection = $getSelection();
      $setBlocksType(selection, () => $createQuoteNode());
    });
  };

  const formatCode = () => {
    if (blockType !== "code") {
      editor.update(() => {
        const selection = $getSelection();
        $setBlocksType(selection, () => $createCodeNode());
      });
    }
  };
  const formatSection = (role: string) => {
    editor.dispatchCommand(INSERT_COLLAPSIBLE_COMMAND, role);
  };

  if (isLLM) {
    blockTypeToBlockName.system = "System";
    blockTypeToBlockName.assistant = "Assistant";
    blockTypeToBlockName.user = "User";
  }

  return (
    <Select
      value={blockType}
      disabled={!isEditable}
      onValueChange={(value) => {
        switch (value) {
          case "h1":
            formatHeading("h1");
            break;
          case "h2":
            formatHeading("h2");
            break;
          case "h3":
            formatHeading("h3");
            break;
          case "h4":
            formatHeading("h4");
            break;
          case "h5":
            formatHeading("h5");
            break;
          case "h6":
            formatHeading("h6");
            break;
          case "paragraph":
            formatParagraph();
            break;
          case "number":
            formatOrderedList();
            break;
          case "bullet":
            formatUnorderedList();
            break;
          case "quote":
            formatQuote();
            break;
          case "code":
            formatCode();
            break;
          case "system":
            formatSection("system");
            break;
          case "assistant":
            formatSection("assistant");
            break;
          case "user":
            formatSection("user");
            break;
        }
      }}
    >
      <SelectTrigger className="w-40">
        <SelectValue placeholder="Block Type" />
      </SelectTrigger>

      <SelectContent onCloseAutoFocus={() => editor.focus()}>
        {Object.keys(blockTypeToBlockName).map((blockType) => {
          return (
            <SelectItem key={blockType} value={blockType}>
              {blockTypeToBlockName[blockType]}
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
};
