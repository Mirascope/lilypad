import { CodeBlock } from "@/components/CodeBlock";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { diffArrays } from "diff";
import { useState } from "react";

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

/**
 * Add line highlighting using Shiki's [!code highlight] comments
 */
const addHighlightComments = (
  lines: string[],
  lineHighlights: Record<number, string>
): string => {
  return lines
    .map((line, index) => {
      // Line numbers are 1-based
      const lineNumber = index + 1;
      if (lineHighlights[lineNumber]) {
        if (lineHighlights[lineNumber] === "added") {
          return `${line} // [!code ++]`;
        } else if (lineHighlights[lineNumber] === "removed") {
          return `${line} // [!code --]`;
        } else {
          return `${line} // [!code highlight]`;
        }
      }
      return line;
    })
    .join("\n");
};

interface CodeBlockWithLineNumbersSideBySideProps {
  diffedLines: DiffPart[];
  language?: string;
}

const CodeBlockWithLineNumbersSideBySide = ({
  diffedLines,
  language = "typescript",
}: CodeBlockWithLineNumbersSideBySideProps) => {
  const processedData = processDiffData(diffedLines);

  const renderColumn = (side: "before" | "after") => {
    let lineNumber = 0;
    const codeLines: string[] = [];
    const lineHighlights: Record<number, string> = {};

    processedData.forEach((block) => {
      const lines = side === "before" ? block.oldValue : block.newValue;

      lines.forEach((line) => {
        if (line !== PLACEHOLDER) {
          lineNumber++;
          codeLines.push(typeof line === "symbol" ? "" : line);

          // Apply highlighting based on diff type
          if (
            (block.type === "modified" &&
              ((side === "before" &&
                !block.oldValue.every((v) => v === PLACEHOLDER)) ||
                (side === "after" &&
                  !block.newValue.every((v) => v === PLACEHOLDER)))) ||
            (block.type === "added" && side === "after") ||
            (block.type === "removed" && side === "before")
          ) {
            lineHighlights[lineNumber] = "highlight";
          }
        } else {
          // Empty placeholder line
          codeLines.push("");
        }
      });
    });

    // Add the highlight comments and generate the final code string
    const highlightedCode = addHighlightComments(codeLines, lineHighlights);

    return (
      <div className="flex-1 w-full overflow-x-auto">
        <CodeBlock
          code={highlightedCode}
          language={language}
          className={`border-0 ${side === "before" ? "highlight-removed" : "highlight-added"}`}
        />
      </div>
    );
  };

  return (
    <div className="font-mono text-sm border rounded-md overflow-hidden">
      <div className="flex">
        {renderColumn("before")}
        <div className="w-px bg-gray-300"></div>
        {renderColumn("after")}
      </div>
    </div>
  );
};

interface CodeBlockWithLineNumbersAndHighlightsProps {
  diffedLines: DiffPart[];
  language?: string;
}

const CodeBlockWithLineNumbersAndHighlights = ({
  diffedLines,
  language = "python",
}: CodeBlockWithLineNumbersAndHighlightsProps) => {
  // Generate the unified code view
  const codeLines: string[] = [];
  const lineHighlights: Record<number, string> = {};
  let currentLine = 0;

  diffedLines.forEach((part) => {
    const symbol = part.added ? "+" : part.removed ? "-" : " ";

    part.value.forEach((line) => {
      currentLine++;
      codeLines.push(`${symbol} ${line}`);

      if (part.added) {
        lineHighlights[currentLine] = "added";
      }
      if (part.removed) {
        lineHighlights[currentLine] = "removed";
      }
    });
  });

  // Add the highlight comments and generate the final code string
  const highlightedCode = addHighlightComments(codeLines, lineHighlights);

  return (
    <div className="w-full font-mono text-sm border rounded-md overflow-hidden">
      <CodeBlock
        code={highlightedCode}
        language={language}
        className="unified-diff border-0"
      />
    </div>
  );
};

interface DiffToolProps {
  firstCodeBlock: string;
  secondCodeBlock: string;
  language?: string;
}

export const DiffTool = ({
  firstCodeBlock,
  secondCodeBlock,
  language = "typescript",
}: DiffToolProps) => {
  const [mode, setMode] = useState<"split" | "unified">("split");

  const handleModeChange = (checked: boolean) => {
    setMode(checked ? "split" : "unified");
  };

  let diffed: DiffPart[] | null = null;
  if (firstCodeBlock && secondCodeBlock) {
    const firstCode = firstCodeBlock.split("\n");
    const secondCode = secondCodeBlock.split("\n");
    diffed = diffArrays(firstCode, secondCode);
  }

  return (
    <>
      {diffed && (
        <>
          <div className="flex items-center space-x-2">
            <Switch
              id="diff-view"
              checked={mode === "split"}
              onCheckedChange={handleModeChange}
            />
            <Label htmlFor="diff-view">
              {mode === "split" ? "Split" : "Unified"} View
            </Label>
          </div>
          <div className="flex w-full">
            {mode === "unified" ? (
              <CodeBlockWithLineNumbersAndHighlights
                diffedLines={diffed}
                language={language}
              />
            ) : (
              <CodeBlockWithLineNumbersSideBySide
                diffedLines={diffed}
                language={language}
              />
            )}
          </div>
        </>
      )}
    </>
  );
};
