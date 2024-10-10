import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { INSERT_COLLAPSIBLE_COMMAND } from "@/components/lexical/collapsible-plugin";
import { useEffect, useState } from "react";
import { $getSelection, $isRangeSelection } from "lexical";
import { $findMatchingParent } from "@lexical/utils";
import { $isCollapsibleContainerNode } from "@/components/lexical/collapsible-container-node";

export const messageTypeToMessageName: Record<string, string> = {
  System: "SYSTEM",
  Assistant: "ASSISTANT",
  User: "USER",
};

export const MessageTypeDropdown = () => {
  const [editor] = useLexicalComposerContext();
  const [messageType, setMessageType] = useState<
    keyof typeof messageTypeToMessageName | undefined
  >(undefined);
  const [isCursorInsideCollapsible, setIsCursorInsideCollapsible] =
    useState<boolean>(false);

  useEffect(() => {
    // Listener to detect cursor position within the editor
    const removeUpdateListener = editor.registerUpdateListener(
      ({ editorState }) => {
        editorState.read(() => {
          const selection = $getSelection();

          if ($isRangeSelection(selection)) {
            const anchorNode = selection.anchor.getNode();
            // Check if the cursor is inside a CollapsibleContainerNode
            const collapsibleContainer = $findMatchingParent(
              anchorNode,
              $isCollapsibleContainerNode
            );
            setIsCursorInsideCollapsible(!!collapsibleContainer);
          } else {
            setIsCursorInsideCollapsible(false);
          }
        });
      }
    );

    return () => {
      removeUpdateListener();
    };
  }, [editor]);

  const formatSection = (role: string) => {
    setMessageType(undefined);
    editor.dispatchCommand(INSERT_COLLAPSIBLE_COMMAND, role);
  };
  return (
    <Select
      value={messageType || ""}
      onValueChange={(value) => {
        formatSection(value);
      }}
    >
      <SelectTrigger className='w-40' disabled={isCursorInsideCollapsible}>
        <SelectValue placeholder='Messages' />
      </SelectTrigger>

      <SelectContent onCloseAutoFocus={() => editor.focus()}>
        {Object.keys(messageTypeToMessageName).map((messageType) => {
          return (
            <SelectItem
              key={messageType}
              value={messageTypeToMessageName[messageType]}
            >
              {messageType}
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
};