import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import {
  LexicalTypeaheadMenuPlugin,
  MenuOption,
  TriggerFn,
} from "@lexical/react/LexicalTypeaheadMenuPlugin";
import { TextNode } from "lexical";
import { JSX, useCallback, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { $createTemplateNode } from "./template-node";

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
  return (
    <li
      key={option.key}
      tabIndex={-1}
      className={`
        px-3 py-2 mx-1 my-0.5 text-sm cursor-pointer rounded-md
        transition-colors duration-150 ease-in-out flex items-center
        ${
          isSelected
            ? "bg-blue-50 text-blue-700"
            : "text-gray-700 hover:bg-gray-50"
        }
      `}
      ref={option.setRefElement}
      role="option"
      aria-selected={isSelected}
      id={`typeahead-item-${index}`}
      onMouseEnter={onMouseEnter}
      onClick={onClick}
    >
      <span className="popper__reference truncate">
        {option.metadata.value}
      </span>
    </li>
  );
}

export const TemplateSuggestionPlugin = ({
  inputs,
  inputValues,
}: {
  inputs: string[];
  inputValues: Record<string, any>;
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
        const value = inputValues[selectedOption.metadata.value];
        const templateNode = $createTemplateNode(selectedOption.key, value);
        if (nodeToReplace) {
          nodeToReplace.replace(templateNode);
        }
        templateNode.select();
        closeMenu();
      });
    },
    [editor, inputValues]
  );

  const createFilteredOptions = (options: Template[], query: string | null) => {
    // Return first 10 options if no query
    if (!query || query.trim() === "") {
      return options.slice(0, 10);
    }

    // Create a case-sensitive regex from the query string
    const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

    // Filter by both key and display value with case sensitivity
    return options
      .filter(
        (option) =>
          regex.test(option.key) ||
          (option.metadata && regex.test(option.metadata.value))
      )
      .slice(0, 10);
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
          <div className="bg-background rounded-md shadow-lg max-h-[320px] overflow-y-auto w-[180px] min-w-[90px] border border-gray-100">
            <ul className="px-1.5">
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
      anchorClassName="z-10000"
      menuRenderFn={renderSuggestionsMenu}
    />
  );
};
