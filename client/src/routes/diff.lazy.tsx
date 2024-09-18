import { diffArrays } from "diff";

import { createLazyFileRoute } from "@tanstack/react-router";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useState } from "react";
export const Route = createLazyFileRoute("/diff")({
  component: () => <Comparison />,
});
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
      result.push({
        type: "removed",
        value: current.value,
      });
      i++;
    } else if (current.added) {
      // This is an addition
      result.push({
        type: "added",
        value: current.value,
      });
      i++;
    } else {
      // This is an unchanged line
      result.push({
        type: "unchanged",
        value: current.value,
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
      const lines =
        side === "before"
          ? block.oldValue || block.value
          : block.newValue || block.value;

      if (!lines && side === "before" && block.type === "added") return;
      if (!lines && side === "after" && block.type === "removed") return;

      lines.forEach((line, lineIndex) => {
        console.log(line);
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
              : block.type === "added"
                ? "bg-green-100"
                : block.type === "removed"
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

const Comparison = () => {
  const [mode, setMode] = useState("split");
  const first = [
    `@openai.call(model="gpt-4o", tools=[format_book])`,
    `@prompt_template("Recommend a {genre} book.")`,
    `def recommend_book(genre: str): ...`,
    `def foo(): ...`,
  ];
  const second = [
    `@openai.call(model="gpt-4o", tools=[format_book])`,
    `@prompt_template(`,
    `"""`,
    `SYSTEM:`,
    ``,
    `You are an expert web searcher. Your task is to answer the user's question using the provided tools.`,
    `"""`,
    `)`,
    `def recommend_book(genre: str, topic: str): ...`,
    `def foo(): ...`,
  ];

  const diffed = diffArrays(first, second);
  const handleModeChange = (checked: boolean) => {
    setMode(checked ? "split" : "unified");
  };
  return (
    <div>
      <div className='flex items-center space-x-2'>
        <Switch
          id='diff-view'
          checked={mode === "split"}
          onCheckedChange={handleModeChange}
        />
        <Label htmlFor='diff-view'>Diff View</Label>
      </div>
      <div className='flex'>
        {mode === "unified" ? (
          <CodeBlockWithLineNumbersAndHighlights diffedLines={diffed} />
        ) : (
          <CodeBlockWithLineNumbersSideBySide diffedLines={diffed} />
        )}
      </div>
    </div>
  );
};
