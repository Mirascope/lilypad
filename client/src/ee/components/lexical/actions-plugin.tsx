import type { LexicalEditor } from "lexical";
import type { JSX } from "react";

import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { CLEAR_EDITOR_COMMAND } from "lexical";
import { useEffect, useState } from "react";

import LilypadDialog from "@/components/LilypadDialog";
import { Button } from "@/components/ui/button";
import { DialogClose, DialogFooter } from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { TOGGLE_SHOW_VARIABLE_COMMAND } from "@/ee/components/lexical/template-plugin";
import { Braces, Eye, LetterText, ListRestart, Pencil } from "lucide-react";

export const ActionsPlugin = ({
  isDisabled,
}: {
  isDisabled: boolean;
}): JSX.Element => {
  const [editor] = useLexicalComposerContext();
  const [isEditable, setIsEditable] = useState<boolean>(!isDisabled);
  const [isShowingVariable, setIsShowingVariable] = useState(true);

  useEffect(() => {
    if (isDisabled === true) {
      editor.setEditable(false);
      setIsEditable(false);
    } else if (isDisabled === false) {
      editor.setEditable(true);
      setIsEditable(true);
    }

    const removeListener = editor.registerEditableListener((editable) => {
      if (isDisabled !== true) {
        setIsEditable(editable);
      } else if (editable) {
        // If we're supposed to be disabled but somehow became editable
        editor.setEditable(false);
      }
    });

    return removeListener;
  }, [editor, isDisabled]);

  const toggleEditable = () => {
    // Only allow toggling if not disabled
    if (isDisabled !== true) {
      const newState = !editor.isEditable();
      editor.setEditable(newState);
      // Also update our local state to keep things in sync
      setIsEditable(newState);
    }
  };

  return (
    <div className='flex justify-end gap-2 p-2'>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type='button'
            variant='outline'
            size='icon'
            onClick={() => {
              editor.dispatchCommand(
                TOGGLE_SHOW_VARIABLE_COMMAND,
                !isShowingVariable
              );
              setIsShowingVariable(!isShowingVariable);
            }}
          >
            {!isShowingVariable ? (
              <LetterText strokeWidth={1.5} color={"hsl(123 47% 34%)"} />
            ) : (
              <Braces strokeWidth={1.5} color={"hsl(239, 84%, 67%)"} />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {!isShowingVariable ? "Values" : "Variables"}
        </TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type='button'
            variant='outline'
            size='icon'
            disabled={isDisabled === true}
            onClick={toggleEditable}
          >
            {!isEditable ? (
              <Eye strokeWidth={1.5} />
            ) : (
              <Pencil strokeWidth={1.5} />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {!isEditable ? "Read-only" : "Editable"}
        </TooltipContent>
      </Tooltip>
      <LilypadDialog
        icon={<ListRestart strokeWidth={1.5} />}
        tooltipContent='Clear editor'
        title='Clear editor'
        description="This will clear the editor's contents."
        buttonProps={{
          type: "button",
          disabled: isDisabled,
        }}
      >
        <ShowClearDialog editor={editor} />
      </LilypadDialog>
    </div>
  );
};

function ShowClearDialog({ editor }: { editor: LexicalEditor }): JSX.Element {
  return (
    <>
      <div className='py-4'>Are you sure you want to clear the editor?</div>
      <DialogFooter>
        <DialogClose asChild>
          <Button
            type='button'
            variant='destructive'
            onClick={() => {
              editor.dispatchCommand(CLEAR_EDITOR_COMMAND, undefined);
              editor.focus();
            }}
          >
            Clear
          </Button>
        </DialogClose>
        <DialogClose asChild>
          <Button
            type='button'
            variant='outline'
            onClick={() => {
              editor.focus();
            }}
          >
            Cancel
          </Button>
        </DialogClose>
      </DialogFooter>
    </>
  );
}
