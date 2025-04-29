import {
  $getSelection,
  $isRangeSelection,
  $isRootOrShadowRoot,
  CAN_REDO_COMMAND,
  CAN_UNDO_COMMAND,
  COMMAND_PRIORITY_CRITICAL,
  FORMAT_TEXT_COMMAND,
  REDO_COMMAND,
  SELECTION_CHANGE_COMMAND,
  UNDO_COMMAND,
} from "lexical";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Toggle } from "@/components/ui/toggle";
import { $isListNode, ListNode } from "@lexical/list";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { $isHeadingNode } from "@lexical/rich-text";
import {
  $findMatchingParent,
  $getNearestNodeOfType,
  mergeRegister,
} from "@lexical/utils";
import {
  CodeIcon,
  FontBoldIcon,
  FontItalicIcon,
  ReloadIcon,
  UnderlineIcon,
} from "@radix-ui/react-icons";

import { BlockTypeDropdown, blockTypeToBlockName } from "./block-type-dropdown";
import { MessageTypeDropdown } from "./messages-dropdown";

export const ToolbarPlugin = ({ isLLM = false }: { isLLM: boolean }) => {
  const [editor] = useLexicalComposerContext();
  const [isEditable, setIsEditable] = useState(() => editor.isEditable());
  const [isBold, setIsBold] = useState<boolean>(false);
  const [isItalic, setIsItalic] = useState<boolean>(false);
  const [isUnderline, setIsUnderline] = useState<boolean>(false);
  const [isCode, setIsCode] = useState<boolean>(false);
  const [blockType, setBlockType] =
    useState<keyof typeof blockTypeToBlockName>("paragraph");

  const [canUndo, setCanUndo] = useState<boolean>(false);
  const [canRedo, setCanRedo] = useState<boolean>(false);

  const $updateToolbar = useCallback(() => {
    const selection = $getSelection();
    if ($isRangeSelection(selection)) {
      setIsBold(selection.hasFormat("bold"));
      setIsItalic(selection.hasFormat("italic"));
      setIsUnderline(selection.hasFormat("underline"));
      setIsCode(selection.hasFormat("code"));

      const anchorNode = selection.anchor.getNode();

      let element =
        anchorNode.getKey() === "root"
          ? anchorNode
          : $findMatchingParent(anchorNode, (e) => {
              const parent = e.getParent();
              return parent !== null && $isRootOrShadowRoot(parent);
            });

      if (element === null) {
        element = anchorNode.getTopLevelElementOrThrow();
      }

      const elementDOM = editor.getElementByKey(element.getKey());

      if (elementDOM !== null) {
        if ($isListNode(element)) {
          const parentList = $getNearestNodeOfType<ListNode>(
            anchorNode,
            ListNode
          );
          const type = parentList
            ? parentList.getListType()
            : element.getListType();
          setBlockType(type);
        } else {
          const type = $isHeadingNode(element)
            ? element.getTag()
            : element.getType();
          if (type in blockTypeToBlockName) {
            setBlockType(type as keyof typeof blockTypeToBlockName);
          }
        }
      }
    }
  }, [editor]);

  useEffect(() => {
    return mergeRegister(
      editor.registerCommand(
        SELECTION_CHANGE_COMMAND,
        () => {
          $updateToolbar();
          return false;
        },
        COMMAND_PRIORITY_CRITICAL
      ),
      editor.registerUpdateListener(({ editorState }) => {
        editorState.read(() => {
          $updateToolbar();
        });
      })
    );
  }, [editor, $updateToolbar]);

  useEffect(() => {
    return mergeRegister(
      editor.registerEditableListener((editable) => {
        setIsEditable(editable);
      }),
      editor.registerCommand(
        CAN_UNDO_COMMAND,
        (payload) => {
          setCanUndo(payload);
          return false;
        },
        COMMAND_PRIORITY_CRITICAL
      ),
      editor.registerCommand(
        CAN_REDO_COMMAND,
        (payload) => {
          setCanRedo(payload);
          return false;
        },
        COMMAND_PRIORITY_CRITICAL
      )
    );
  }, [editor]);

  return (
    <div className="w-full border-b z-10 relative">
      <div className="flex space-x-2 justify-center p-1">
        <Button
          className="h-8 px-2"
          variant="ghost"
          disabled={!canUndo || !isEditable}
          onClick={() => editor.dispatchCommand(UNDO_COMMAND, undefined)}
        >
          {/* reload flip to left */}
          <ReloadIcon className="transform -scale-x-100" />
        </Button>

        <Button
          className="h-8 px-2"
          variant="ghost"
          disabled={!canRedo || !isEditable}
          onClick={() => editor.dispatchCommand(REDO_COMMAND, undefined)}
        >
          <ReloadIcon />
        </Button>

        <Separator orientation="vertical" className="h-auto my-1" />

        <BlockTypeDropdown blockType={blockType} isEditable={isEditable} />

        <Separator orientation="vertical" className="h-auto my-1" />

        <Toggle
          area-label="Bold"
          size="sm"
          pressed={isBold}
          onPressedChange={(pressed) => {
            editor.dispatchCommand(FORMAT_TEXT_COMMAND, "bold");
            setIsBold(pressed);
          }}
          disabled={!isEditable}
        >
          <FontBoldIcon />
        </Toggle>

        <Toggle
          area-label="Italic"
          size="sm"
          pressed={isItalic}
          onPressedChange={(pressed) => {
            editor.dispatchCommand(FORMAT_TEXT_COMMAND, "italic");
            setIsItalic(pressed);
          }}
          disabled={!isEditable}
        >
          <FontItalicIcon />
        </Toggle>

        <Toggle
          area-label="Underline"
          size="sm"
          pressed={isUnderline}
          onPressedChange={(pressed) => {
            editor.dispatchCommand(FORMAT_TEXT_COMMAND, "underline");
            setIsUnderline(pressed);
          }}
          disabled={!isEditable}
        >
          <UnderlineIcon />
        </Toggle>
        <Toggle
          area-label="Inline Code"
          size="sm"
          pressed={isCode}
          onPressedChange={(pressed) => {
            editor.dispatchCommand(FORMAT_TEXT_COMMAND, "code");
            setIsCode(pressed);
          }}
          disabled={!isEditable}
        >
          <CodeIcon />
        </Toggle>
        {isLLM && (
          <>
            <Separator orientation="vertical" className="h-auto my-1" />
            <MessageTypeDropdown isEditable={isEditable} />
          </>
        )}
      </div>
    </div>
  );
};
