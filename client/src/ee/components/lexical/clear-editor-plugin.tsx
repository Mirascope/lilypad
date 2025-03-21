/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 */

import { useLayoutEffect, type JSX } from "react";

import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import {
  $createParagraphNode,
  $getRoot,
  $getSelection,
  $isRangeSelection,
  CLEAR_EDITOR_COMMAND,
  COMMAND_PRIORITY_EDITOR,
} from "lexical";

type Props = Readonly<{
  onClear?: () => void;
}>;

export const ClearEditorPlugin = ({ onClear }: Props): JSX.Element | null => {
  const [editor] = useLexicalComposerContext();

  useLayoutEffect(() => {
    return editor.registerCommand(
      CLEAR_EDITOR_COMMAND,
      (_payload) => {
        editor.update(() => {
          if (onClear == null) {
            const root = $getRoot();
            const selection = $getSelection();
            const paragraph = $createParagraphNode();
            root.clear();
            root.append(paragraph);

            if (selection !== null) {
              paragraph.select();
            }
            if ($isRangeSelection(selection)) {
              selection.format = 0;
            }
          } else {
            onClear();
          }
        });
        return true;
      },
      COMMAND_PRIORITY_EDITOR
    );
  }, [editor, onClear]);

  return null;
};
