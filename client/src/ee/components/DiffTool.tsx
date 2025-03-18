import { CodeSnippet } from "@/components/CodeSnippet";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { diffArrays } from "diff";
import { JSX, useState } from "react";

// Define the placeholder symbol
const PLACEHOLDER = Symbol("placeholder");

// Define types for diff data
type DiffType = "modified" | "removed" | "added" | "unchanged";

interface DiffPart {
  value: string[];
  added?: boolean;
  removed?: boolean;
}

interface ProcessedDiffBlock {
  type: DiffType;
  oldValue: (string | symbol)[];
  newValue: (string | symbol)[];
}

/**
 * Process diffed lines into a more structured format for rendering
 */
const processDiffData = (diffedLines: DiffPart[]): ProcessedDiffBlock[] => {
  const result: ProcessedDiffBlock[] = [];
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

interface CodeBlockWithLineNumbersSideBySideProps {
  diffedLines: DiffPart[];
}

const CodeBlockWithLineNumbersSideBySide = ({
  diffedLines,
}: CodeBlockWithLineNumbersSideBySideProps) => {
  const processedData = processDiffData(diffedLines);

  const renderColumn = (side: "before" | "after") => {
    let lineNumber = 0;
    const lineNumbers: JSX.Element[] = [];
    const codeLines: string[] = [];
    const lineHighlights: Record<number, string> = {};

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

          codeLines.push(typeof line === "symbol" ? "" : (line as string));

          // Apply highlighting based on diff type
          const bgColor =
            block.type === "modified"
              ? side === "before"
                ? "bg-red-100"
                : "bg-green-100"
              : block.type === "added" && side === "after"
                ? "bg-green-100"
                : block.type === "removed" && side === "before"
                  ? "bg-red-100"
                  : "";

          if (bgColor) {
            lineHighlights[lineNumber] = bgColor;
          }
        } else {
          lineNumbers.push(
            <div
              key={`${side}-linenumber-placeholder-${blockIndex}-${lineIndex}`}
              className='text-xs leading-5 text-gray-500 py-[1px]'
            >
              &nbsp;
            </div>
          );
          codeLines.push("");
        }
      });
    });

    // Custom line numbers component
    const customLineNumbers = (
      <div className='flex-none w-12 text-right pr-2 bg-gray-100 border-r border-gray-300'>
        {lineNumbers}
      </div>
    );

    return (
      <div className='flex-1 overflow-x-auto'>
        <CodeSnippet
          code={codeLines.join("\n")}
          showCopyButton={false}
          customLineNumbers={customLineNumbers}
          lineHighlights={lineHighlights}
          className='!p-0 !bg-transparent'
          wrapperClassName='border-0'
        />
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

interface CodeBlockWithLineNumbersAndHighlightsProps {
  diffedLines: DiffPart[];
}

const CodeBlockWithLineNumbersAndHighlights = ({
  diffedLines,
}: CodeBlockWithLineNumbersAndHighlightsProps) => {
  let beforeLineNumber = 0;
  let afterLineNumber = 0;

  // Generate the unified code view
  const codeLines: string[] = [];
  const lineHighlights: Record<number, string> = {};
  let currentLine = 0;

  diffedLines.forEach((part) => {
    const symbol = part.added ? "+" : part.removed ? "-" : " ";
    const bgColor = part.added
      ? "bg-green-100"
      : part.removed
        ? "bg-red-100"
        : "";

    part.value.forEach((line) => {
      currentLine++;
      codeLines.push(`${symbol} ${line}`);

      if (bgColor) {
        lineHighlights[currentLine] = bgColor;
      }
    });
  });

  // Generate line numbers for both sides
  const renderLineNumbers = () => {
    const beforeNumbers: JSX.Element[] = [];
    const afterNumbers: JSX.Element[] = [];

    diffedLines.forEach((part) => {
      if ((!part.added && !part.removed) || part.removed) {
        part.value.forEach(() => {
          beforeLineNumber++;
          beforeNumbers.push(
            <div
              key={`before-${beforeLineNumber}`}
              className='py-0.5 text-gray-500'
            >
              {beforeLineNumber}
            </div>
          );
        });
      } else {
        part.value.forEach((_, i) => {
          beforeNumbers.push(
            <div
              key={`after-empty-${beforeLineNumber}-${i}`}
              className='py-0.5'
            >
              &nbsp;
            </div>
          );
        });
      }
    });

    diffedLines.forEach((part) => {
      if ((!part.added && !part.removed) || part.added) {
        part.value.forEach(() => {
          afterLineNumber++;
          afterNumbers.push(
            <div
              key={`after-${afterLineNumber}`}
              className='py-0.5 text-gray-500'
            >
              {afterLineNumber}
            </div>
          );
        });
      } else {
        part.value.forEach((_, i) => {
          afterNumbers.push(
            <div key={`after-empty-${afterLineNumber}-${i}`} className='py-0.5'>
              &nbsp;
            </div>
          );
        });
      }
    });

    return (
      <div className='flex gap-1 w-12 pl-1 bg-gray-100 border-r border-gray-300'>
        <div>{beforeNumbers}</div>
        <div>{afterNumbers}</div>
      </div>
    );
  };

  return (
    <div className='font-mono text-sm border rounded-md overflow-hidden'>
      <CodeSnippet
        code={codeLines.join("\n")}
        showCopyButton={false}
        customLineNumbers={renderLineNumbers()}
        lineHighlights={lineHighlights}
        className='!p-0 !bg-transparent'
        wrapperClassName='border-0'
      />
    </div>
  );
};

interface DiffToolProps {
  firstLexicalClosure: string;
  secondLexicalClosure: string;
  language?: string; // Added to support different languages
}

export const DiffTool = ({
  firstLexicalClosure,
  secondLexicalClosure,
  language = "python", // Default to python for backward compatibility
}: DiffToolProps) => {
  const [mode, setMode] = useState<"split" | "unified">("split");

  const handleModeChange = (checked: boolean) => {
    setMode(checked ? "split" : "unified");
  };

  let diffed: DiffPart[] | null = null;
  if (firstLexicalClosure && secondLexicalClosure) {
    const firstClosure = firstLexicalClosure.split("\n");
    const secondClosure = secondLexicalClosure.split("\n");
    diffed = diffArrays(firstClosure, secondClosure);
  }

  return (
    <>
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
