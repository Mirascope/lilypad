import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import {
  LexicalTypeaheadMenuPlugin,
  MenuOption,
} from "@lexical/react/LexicalTypeaheadMenuPlugin";
import { TextNode } from "lexical";
import { useCallback, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { $createTemplateNode } from "./template-node";
import { TriggerFn } from "@lexical/react/LexicalTypeaheadMenuPlugin";

const PUNCTUATION =
  "\\.,\\+\\*\\?\\$\\@\\|#{}\\(\\)\\^\\-\\[\\]\\\\/!%'\"~=<>_:;";

const useBasicTypeaheadTriggerMatch = (
  trigger: string,
  { minLength = 1, maxLength = 75 }: { minLength?: number; maxLength?: number }
): TriggerFn => {
  return useCallback(
    (text: string) => {
      const validChars = "[^" + trigger + PUNCTUATION + "\\s]";
      const TypeaheadTriggerRegex = new RegExp(
        "(^||\\()(" +
          "[" +
          trigger +
          "]" +
          "((?:" +
          validChars +
          "){0," +
          maxLength +
          "})" +
          ")$"
      );
      const match = TypeaheadTriggerRegex.exec(text);
      if (match !== null) {
        const maybeLeadingWhitespace = match[1];
        const matchingString = match[3];
        if (matchingString.length >= minLength) {
          return {
            leadOffset: match.index + maybeLeadingWhitespace.length,
            matchingString,
            replaceableString: match[2],
          };
        }
      }
      return null;
    },
    [maxLength, minLength, trigger]
  );
};

type Template = {
  key: string;
  metadata: {
    id: string;
    value: string;
  };
};

// Class representing a typeahead option
class CustomTypeaheadOption extends MenuOption {
  key: string;
  metadata: {
    id: string;
    value: string;
  };

  constructor(key: string, metadata: { id: string; value: string }) {
    super(key);
    this.key = key;
    this.metadata = metadata;
  }
}

// Suggestion item component
export function SuggestionItem({
  index,
  isSelected,
  onClick,
  onMouseEnter,
  option,
}: {
  index: number;
  isSelected: boolean;
  onClick: () => void;
  onMouseEnter: () => void;
  option: CustomTypeaheadOption;
}): JSX.Element {
  let className =
    "cursor-pointer bg-slate-50 text-unique-600 hover:bg-secondary-50 py-2 px-3 text-xs flex items-center";
  if (isSelected) {
    className += " bg-slate-200";
  }
  return (
    <li
      key={option.key}
      tabIndex={-1}
      className={className}
      ref={option.setRefElement}
      role='option'
      aria-selected={isSelected}
      id={"typeahead-item-" + index}
      onMouseEnter={onMouseEnter}
      onClick={onClick}
    >
      <span className='popper__reference'>{option.metadata.value}</span>
    </li>
  );
}

export const TemplateSuggestionPlugin = ({
  inputs,
}: {
  inputs: string[];
}): JSX.Element | null => {
  const template: Template[] = inputs.map((input: string) => ({
    key: `{${input}}`,
    metadata: { id: "1", value: input },
  }));
  const [editor] = useLexicalComposerContext();
  const [queryString, setQueryString] = useState<string | null>(null);
  const [showTemplateSuggestions, setShowTemplateSuggestions] = useState(true);

  const checkForTriggerMatch = useBasicTypeaheadTriggerMatch("{", {
    minLength: 0,
  });

  const checkForTemplateTriggerMatch = useCallback(
    (text: string) => {
      const match = checkForTriggerMatch(text, editor);
      if (match !== null) {
        setShowTemplateSuggestions(true);
      }
      return match;
    },
    [checkForTriggerMatch, editor]
  );

  const onSelectOption = useCallback(
    (
      selectedOption: CustomTypeaheadOption,
      nodeToReplace: TextNode | null,
      closeMenu: () => void
    ) => {
      editor.update(() => {
        const templateNode = $createTemplateNode(selectedOption.key);
        if (nodeToReplace) {
          nodeToReplace.replace(templateNode);
        }
        templateNode.select();
        closeMenu();
      });
    },
    [editor]
  );

  const createFilteredOptions = (
    options: Template[],
    queryString: string | RegExp | null
  ) => {
    if (queryString === null) {
      return options.slice(0, 10);
    }

    const regex = new RegExp(queryString, "gi");
    return options.filter((option) => regex.test(option.key)).slice(0, 10);
  };

  const options: CustomTypeaheadOption[] = useMemo(
    () =>
      createFilteredOptions(template, queryString).map(
        (data) => new CustomTypeaheadOption(data.key, data.metadata)
      ),
    [template, queryString]
  );

  const renderSuggestionsMenu = (
    anchorElementRef: { current: Element | DocumentFragment | null },
    { selectedIndex, selectOptionAndCleanUp, setHighlightedIndex }: any
  ) => {
    if (
      !showTemplateSuggestions ||
      anchorElementRef.current == null ||
      options.length === 0
    ) {
      return null;
    }
    return anchorElementRef.current && options.length
      ? createPortal(
          <div className='bg-white rounded overflow-hidden shadow-md gap-0.5 max-h-[320px] overflow-y-auto w-[180px] min-w-[90px]'>
            <ul>
              {options.map((option: CustomTypeaheadOption, index: number) => (
                <SuggestionItem
                  index={index}
                  key={index}
                  isSelected={selectedIndex === index}
                  onClick={() => {
                    setHighlightedIndex(index);
                    selectOptionAndCleanUp(option);
                  }}
                  onMouseEnter={() => {
                    setHighlightedIndex(index);
                  }}
                  option={option}
                />
              ))}
            </ul>
          </div>,
          anchorElementRef.current
        )
      : null;
  };

  return (
    <LexicalTypeaheadMenuPlugin<CustomTypeaheadOption>
      onQueryChange={setQueryString}
      onSelectOption={onSelectOption}
      triggerFn={checkForTemplateTriggerMatch}
      options={options}
      anchorClassName='z-[10000]'
      menuRenderFn={renderSuggestionsMenu}
    />
  );
};
