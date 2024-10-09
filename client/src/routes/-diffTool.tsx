import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { FnParamsTable } from "@/types/types";
import { diffArrays } from "diff";
import { Combobox } from "@/components/ui/combobox";

const PLACEHOLDER = Symbol("placeholder");
const processDiffData = (diffedLines) => {
  const result = [];
  let i = 0;

  while (i < diffedLines.length) {
    const current = diffedLines[i];

    if (
      current.removed &&
      i + 1 < diffedLines.length &&
      diffedLines[i + 1].added
    ) {
      // This is a modification (paired removal and addition)
      const oldValue = current.value;
      const newValue = diffedLines[i + 1].value;
      const maxLength = Math.max(oldValue.length, newValue.length);

      result.push({
        type: "modified",
        oldValue: oldValue.concat(
          Array(maxLength - oldValue.length).fill(PLACEHOLDER)
        ),
        newValue: newValue.concat(
          Array(maxLength - newValue.length).fill(PLACEHOLDER)
        ),
      });
      i += 2; // Skip the next item as we've processed it
    } else if (current.removed) {
      // This is a removal
      const oldValue = current.value;
      const newValue = Array(oldValue.length).fill(PLACEHOLDER);
      result.push({
        type: "removed",
        oldValue,
        newValue,
      });
      i++;
    } else if (current.added) {
      // This is an addition
      const newValue = current.value;
      const oldValue = Array(newValue.length).fill(PLACEHOLDER);
      result.push({
        type: "added",
        oldValue,
        newValue,
      });
      i++;
    } else {
      // This is an unchanged line
      result.push({
        type: "unchanged",
        oldValue: current.value,
        newValue: current.value,
      });
      i++;
    }
  }

  return result;
};

const CodeBlockWithLineNumbersSideBySide = ({ diffedLines }) => {
  const processedData = processDiffData(diffedLines);
  const renderColumn = (side) => {
    const code = [];
    let lineNumber = 0;
    const lineNumbers = [];

    processedData.forEach((block, blockIndex) => {
      const lines = side === "before" ? block.oldValue : block.newValue;

      lines.forEach((line, lineIndex) => {
        if (line !== PLACEHOLDER) {
          lineNumber++;
          lineNumbers.push(
            <div
              key={`${side}-linenumber-${lineNumber}`}
              className='text-xs leading-5 text-gray-500 py-[1px]'
            >
              {lineNumber}
            </div>
          );
        } else {
          lineNumbers.push(
            <div
              key={`${side}-linenumber-placeholder-${blockIndex}-${lineIndex}`}
              className='text-xs leading-5 text-gray-500 py-[1px]'
            >
              &nbsp;
            </div>
          );
        }

        const bgColor =
          line === PLACEHOLDER
            ? "bg-gray-200"
            : block.type === "modified"
              ? side === "before"
                ? "bg-red-100"
                : "bg-green-100"
              : block.type === "added" && side === "after"
                ? "bg-green-100"
                : block.type === "removed" && side === "before"
                  ? "bg-red-100"
                  : "";

        code.push(
          <div
            key={`${side}-${blockIndex}-${lineIndex}`}
            className={`${bgColor} leading-5 px-4 py-[1px] min-h-[22px]`}
          >
            {line === null ? "" : line}
          </div>
        );
      });
    });

    return (
      <div className='flex-1 overflow-x-auto'>
        <code className='!p-0 !bg-transparent'>
          <div className='flex'>
            <div className='flex-none w-12 text-right pr-2 bg-gray-100 border-r border-gray-300'>
              {lineNumbers}
            </div>
            <pre className='flex-grow !bg-transparent'>{code}</pre>
          </div>
        </code>
      </div>
    );
  };

  return (
    <div className='font-mono text-sm border rounded-md overflow-hidden'>
      <div className='flex'>
        {renderColumn("before")}
        <div className='w-px bg-gray-300'></div>
        {renderColumn("after")}
      </div>
    </div>
  );
};

const CodeBlockWithLineNumbersAndHighlights = ({ diffedLines }) => {
  let beforeLineNumber = 0;
  let afterLineNumber = 0;
  return (
    <div className='font-mono text-sm border rounded-md overflow-hidden'>
      <code className='!p-0 !bg-transparent'>
        <div className='flex'>
          <div className='flex gap-1 w-12 pl-1 bg-gray-100 border-r border-gray-300'>
            <div>
              {diffedLines.map((part, index) => {
                if ((!part.added && !part.removed) || part.removed) {
                  return part.value.map(() => {
                    beforeLineNumber++;
                    return (
                      <div
                        key={`before-${beforeLineNumber}`}
                        className='py-0.5 text-gray-500'
                      >
                        {beforeLineNumber}
                      </div>
                    );
                  });
                } else {
                  return part.value.map((_, i) => {
                    return (
                      <div
                        key={`after-empty-${afterLineNumber + i + 1}`}
                        className='py-0.5'
                      >
                        &nbsp;
                      </div>
                    );
                  });
                }
              })}
            </div>
            <div>
              {diffedLines.map((part, index) => {
                if ((!part.added && !part.removed) || part.added) {
                  return part.value.map(() => {
                    afterLineNumber++;
                    return (
                      <div
                        key={`after-${afterLineNumber}`}
                        className='py-0.5 text-gray-500'
                      >
                        {afterLineNumber}
                      </div>
                    );
                  });
                } else {
                  return part.value.map((_, i) => {
                    return (
                      <div
                        key={`after-empty-${afterLineNumber + i + 1}`}
                        className='py-0.5'
                      >
                        &nbsp;
                      </div>
                    );
                  });
                }
              })}
            </div>
          </div>
          <pre className='flex-grow !bg-transparent overflow-x-auto'>
            {diffedLines.map((part, i) => {
              const bgColor = part.added
                ? "bg-green-100"
                : part.removed
                  ? "bg-red-100"
                  : undefined;
              const symbol = part.added ? "+" : part.removed ? "-" : " ";
              return part.value.map((line, i) => (
                <div key={i} className={`py-0.5 ${bgColor}`}>
                  {symbol} {line}
                </div>
              ));
            })}
          </pre>
        </div>
      </code>
    </div>
  );
};
export const DiffTool = ({ value }: { value: string }) => {
  const [mode, setMode] = useState("split");
  const [firstLexicalClosure, setFirstLexicalClosure] = useState<string>("");
  const [secondLexicalClosure, setSecondLexicalClosure] = useState<string>("");
  const { isPending, error, data } = useQuery<FnParamsTable[]>({
    queryKey: ["fnParams"],
    queryFn: async () => {
      const response = await fetch(`/llm-fns/names`);
      return await response.json();
    },
  });
  if (isPending) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;

  const handleModeChange = (checked: boolean) => {
    setMode(checked ? "split" : "unified");
  };
  let diffed = null;
  if (firstLexicalClosure && secondLexicalClosure) {
    const firstClosure = firstLexicalClosure.split("\n");
    const secondClosure = secondLexicalClosure.split("\n");
    diffed = diffArrays(firstClosure, secondClosure);
  }
  return (
    <>
      <div className='flex gap-2'>
        <div className='flex flex-col'>
          <Label htmlFor='first-lexical-closure'>First Version</Label>
          <Combobox
            items={data.map((item, i) => ({
              value: item.lexical_closure,
              label: i.toString(),
            }))}
            value={firstLexicalClosure}
            setValue={setFirstLexicalClosure}
          />
        </div>
        <div className='flex flex-col'>
          <Label htmlFor='second-lexical-closure'>Second Version</Label>
          <Combobox
            items={data.map((item, i) => ({
              value: item.lexical_closure,
              label: i.toString(),
            }))}
            value={secondLexicalClosure}
            setValue={setSecondLexicalClosure}
          />
        </div>
      </div>
      {diffed && (
        <>
          <div className='flex items-center space-x-2'>
            <Switch
              id='diff-view'
              checked={mode === "split"}
              onCheckedChange={handleModeChange}
            />
            <Label htmlFor='diff-view'>
              {mode === "split" ? "Split" : "Unified"} View
            </Label>
          </div>
          <div className='flex'>
            {mode === "unified" ? (
              <CodeBlockWithLineNumbersAndHighlights diffedLines={diffed} />
            ) : (
              <CodeBlockWithLineNumbersSideBySide diffedLines={diffed} />
            )}
          </div>
        </>
      )}
    </>
  );
};
