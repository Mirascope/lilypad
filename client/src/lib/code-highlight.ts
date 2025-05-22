import { transformerNotationDiff, transformerNotationHighlight } from "@shikijs/transformers";
import { codeToHtml, createHighlighter } from "shiki";

export type HighlightResult = {
  themeHtml: string;
  code: string;
  language: string;
  meta: string;
  highlighted: boolean;
};

const THEME_LIGHT = "github-light";
const THEME_DARK = "github-dark-default";
// Use the v1 matching algorithm to ensure we highlight bare comment lines
// See: https://github.com/shikijs/shiki/issues/1006
// Note: If ever migrating to the v3 algorithm, it will create an off-by-one
// issue with every block like this: # [!code highlight:21]
// (The line counting behavior in v1 is weird with comments, which is the
// motivation for the v3 algorithm.) So change with care.
const MATCH_ALGORITHM = "v1";

function getTransformers() {
  return [
    transformerNotationHighlight({ matchAlgorithm: MATCH_ALGORITHM }),
    transformerNotationDiff({ matchAlgorithm: MATCH_ALGORITHM }),
  ];
}

// Generate HTML for highlighted code
export async function highlightCode(
  code: string,
  language = "text",
  meta = ""
): Promise<HighlightResult> {
  try {
    // Process the code with meta information for line highlighting
    const processedCode = processCodeWithMetaHighlighting(code.trim(), meta, language);

    // Generate HTML for both light and dark themes
    // Using direct codeToHtml call from shiki
    const themeHtml = await codeToHtml(processedCode, {
      lang: language || "text",
      themes: {
        light: THEME_LIGHT,
        dark: THEME_DARK,
      },
      transformers: getTransformers(),
    });

    // Return both versions for theme switching
    return { code, language, meta, themeHtml, highlighted: true };
  } catch (error) {
    console.error(`Error highlighting code with language "${language}":`, error);

    return fallbackHighlighter(code, language, meta);
  }
}

export function fallbackHighlighter(
  code: string,
  language: string = "text",
  meta: string = ""
): HighlightResult {
  const escapedCode = stripHighlightMarkers(code)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

  const lines = escapedCode.split("\n").map((s) => `<span class="line">${s}`);
  const codeHtml = `<code>${lines.join("\n")}</code>`;

  const shikiClass = `shiki shiki-themes ${THEME_LIGHT} ${THEME_DARK} has-highlighted`;
  const shikiBgStyle = "background-color:#fff;--shiki-dark-bg:#0d1117;";
  const shikiColorStyle = "color:#24292e;--shiki-dark-color:#e6edf3;";
  const fallbackHtml = `<pre class="${shikiClass}" style="${shikiBgStyle}${shikiColorStyle}">${codeHtml}</pre>`;
  return { themeHtml: fallbackHtml, code, language, meta, highlighted: false };
}

// Create singleton highlighters for light and dark themes
let syncHighlighter: Awaited<ReturnType<typeof createHighlighter>> | null = null;
let highlighterInitialized = false;
let initializationPromise: Promise<void> | null = null;

// Initialize highlighters - returns a promise that resolves when sync highlighter is ready
export const initializeSynchronousHighlighter = async (): Promise<void> => {
  // If already initialized, return immediately
  if (highlighterInitialized) return Promise.resolve();
  // If initialization is in progress, return the existing promise
  if (initializationPromise) return initializationPromise;

  const langs = ["python", "bash", "text", "javascript", "typescript", "powershell", "json"];
  // Create a new initialization promise
  initializationPromise = (async () => {
    try {
      // Create the light theme highlighter with Python only
      syncHighlighter = await createHighlighter({
        themes: [THEME_LIGHT, THEME_DARK],
        langs,
      });
      // Mark as initialized
      highlighterInitialized = true;
    } catch (error) {
      console.error("Failed to initialize code highlighters:", error);
      // Reset the initialization promise so we can try again
      initializationPromise = null;
    }
  })();

  return initializationPromise;
};

// Synchronous highlighting function
export function highlightCodeSync(code: string, language: string = "text", meta: string = "") {
  // Process the code with meta information for line highlighting
  const processedCode = processCodeWithMetaHighlighting(code.trim(), meta, language);

  // If highlighters aren't initialized, raise an error
  if (!syncHighlighter) {
    throw new Error("Tried to highlight code, but highlighter not initialized");
  }

  const themeHtml = syncHighlighter.codeToHtml(processedCode, {
    lang: language,
    themes: {
      light: THEME_LIGHT,
      dark: THEME_DARK,
    },
    transformers: getTransformers(),
  });

  return { themeHtml, code, language, meta, highlighted: true };
}

// Keep track of the current timeout ID
let syncHighlightingTimeoutId: number | null = null;

// Flag to control always using sync highlighter for initial highilght
let useSyncHighlighterForAllRenders: boolean = false;

export function useSyncHighlighterAlways(bool: boolean): void {
  useSyncHighlighterForAllRenders = bool;
}

export function temporarilyEnableSyncHighlighting(delayMs: number = 100) {
  // Enable sync highlighting
  useSyncHighlighterAlways(true);

  // Clear any existing timeout
  if (syncHighlightingTimeoutId !== null) {
    clearTimeout(syncHighlightingTimeoutId);
    syncHighlightingTimeoutId = null;
  }

  // Set a new timeout - this will be the one that wins
  syncHighlightingTimeoutId = window.setTimeout(() => {
    useSyncHighlighterAlways(false);
    syncHighlightingTimeoutId = null;
  }, delayMs);
}

export function isNextHighlightSync(): boolean {
  return highlighterInitialized && syncHighlighter != null && useSyncHighlighterForAllRenders;
}

export function initialHighlight(
  code: string,
  language: string = "text",
  meta: string = ""
): HighlightResult {
  if (isNextHighlightSync()) {
    try {
      return highlightCodeSync(code, language, meta);
    } catch (error) {
      console.warn("Failed to use sync highlighter, falling back:", error);
      // Fall back to the basic highlighter if sync fails
    }
  }
  return fallbackHighlighter(code, language, meta);
}

/**
 * Strips highlight markers from code for clipboard copying
 * Removes different syntax variations of [!code highlight] comments
 */
export function stripHighlightMarkers(code: string): string {
  if (!code) return code;

  // Process lines individually to better handle edge cases
  const lines = code.split("\n");
  const processedLines = lines
    .map((line) => {
      // Case 1: Line contains only a highlight marker with no code
      if (
        /^\s*(?:\/\/|#|\/\*|\<\!--|\-\-)\s*\[!code highlight:?\d*\](?:\s*\*\/|\s*--\>)?\s*$/.test(
          line
        )
      ) {
        return null; // Remove line for consistency with rendered code
      }

      // Case 2: Line contains code followed by a highlight marker
      if (
        /\S.*\s*(?:\/\/|#|\/\*|\<\!--|\-\-)\s*\[!code highlight\](?:\s*\*\/|\s*--\>)?\s*$/.test(
          line
        )
      ) {
        // Remove the highlight marker but keep the code
        return line.replace(
          /\s*(?:\/\/|#|\/\*|\<\!--|\-\-)\s*\[!code highlight\](?:\s*\*\/|\s*--\>)?\s*$/,
          ""
        );
      }

      // Case 3: Regular line with no highlight marker
      return line;
    })
    .filter((x) => x != null);

  // Join the lines back together, preserving the original line endings
  return processedLines.join("\n");
}

/**
 * Function to parse meta information and add highlighting comments
 * Transforms meta information like {1-3,5} into [!code highlight] comments
 */
export function processCodeWithMetaHighlighting(
  code: string,
  meta: string,
  language: string
): string {
  if (!meta || !meta.includes("{") || !meta.includes("}")) {
    return code;
  }

  // Extract highlight information from meta: language{lines}
  const highlightMatch = /{([^}]+)}/.exec(meta);
  if (!highlightMatch) return code;

  const highlightInfo = highlightMatch[1];
  const lines = code.split("\n");
  const lineHighlights = new Set<number>();

  // Process ranges like 1-3,5,7-9
  highlightInfo.split(",").forEach((part) => {
    if (part.includes("-")) {
      // Handle ranges like 1-3
      const [start, end] = part.split("-").map(Number);
      for (let i = start; i <= end; i++) {
        lineHighlights.add(i);
      }
    } else {
      // Handle single lines like 5
      lineHighlights.add(Number(part));
    }
  });

  // Get the appropriate comment syntax based on language
  const getCommentSyntax = (lang: string): string => {
    // Different comment syntaxes for different languages
    switch (lang.toLowerCase()) {
      case "html":
      case "xml":
      case "svg":
      case "markdown":
      case "md":
        return "<!-- [!code highlight] -->";
      case "css":
      case "scss":
      case "less":
        return "/* [!code highlight] */";
      case "python":
      case "ruby":
      case "shell":
      case "bash":
      case "sh":
      case "yaml":
      case "yml":
        return "# [!code highlight]";
      case "sql":
        return "-- [!code highlight]";
      default:
        // Default to C-style comments (JavaScript, TypeScript, Java, C, C++, etc.)
        return "// [!code highlight]";
    }
  };

  const commentSyntax = getCommentSyntax(language);

  // Add highlight comments to the specified lines
  const processedLines = lines.map((line, index) => {
    const lineNumber = index + 1;
    if (lineHighlights.has(lineNumber)) {
      // Add highlight marker to the end of the line
      if (line.trim() !== "") {
        return `${line} ${commentSyntax}`;
      } else {
        // Handle empty lines - add a space so the marker is visible
        return commentSyntax;
      }
    }
    return line;
  });

  return processedLines.join("\n");
}
