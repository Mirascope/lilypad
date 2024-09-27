import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { useState, useEffect } from "react";
import { $getSelection, $isRangeSelection } from "lexical";
import { KEY_DOWN_COMMAND, COMMAND_PRIORITY_LOW } from "lexical";
import { Popover, PopoverContent } from "@/components/ui/popover";

export const TemplatePlugin = () => {
  const [editor] = useLexicalComposerContext();
  const [isOpen, setIsOpen] = useState(false);
  const [anchorRect, setAnchorRect] = useState(null);

  useEffect(() => {
    const removeListener = editor.registerCommand(
      KEY_DOWN_COMMAND,
      (event) => {
        if (event.key === "{") {
          editor.update(() => {
            const selection = $getSelection();
            if ($isRangeSelection(selection)) {
              const nativeSelection = window.getSelection();
              if (nativeSelection.rangeCount > 0) {
                const domRange = nativeSelection.getRangeAt(0);
                const rect = domRange.getBoundingClientRect();
                setAnchorRect(rect);
                setIsOpen(true);
              }
            }
          });
          return true; // Event handled
        }
        return false; // Event not handled
      },
      COMMAND_PRIORITY_LOW
    );

    return () => {
      removeListener();
    };
  }, [editor]);
  return (
    <>
      {isOpen && anchorRect && (
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverContent
            side='bottom'
            align='start'
            style={{
              position: "absolute",
              top: anchorRect.top + window.scrollY,
              left: anchorRect.left + window.scrollX,
            }}
          >
            {/* Your popover content goes here */}
          </PopoverContent>
        </Popover>
      )}
    </>
  );
};
