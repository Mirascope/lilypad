import { Check, Copy } from "lucide-react";
import { useEffect, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";

export const CodeBlock = ({
  code,
  language,
  filename,
  highlightLines = [],
  showLineNumbers = true,
}: {
  code: string;
  language: string;
  filename: string;
  highlightLines?: number[];
  showLineNumbers?: boolean;
}) => {
  const [copied, setCopied] = useState(false);
  const [currentFontSize, setCurrentFontSize] = useState<string | null>("14px");

  useEffect(() => {
    const updateFontSize = () => {
      if (window.matchMedia("(min-width: 1280px)").matches) {
        setCurrentFontSize("14px");
      } else if (window.matchMedia("(min-width: 1024px)").matches) {
        setCurrentFontSize("13px");
      } else if (window.matchMedia("(min-width: 768px)").matches) {
        setCurrentFontSize("12px");
      } else if (window.matchMedia("(min-width: 640px)").matches) {
        setCurrentFontSize("11px");
      } else if (window.matchMedia("(min-width: 480px)").matches) {
        setCurrentFontSize("10px");
      } else {
        setCurrentFontSize("6px");
      }
    };

    updateFontSize();
    window.addEventListener("resize", updateFontSize);
    return () => window.removeEventListener("resize", updateFontSize);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Get appropriate icon based on language
  const getLanguageIcon = () => {
    if (language === "python" || language === "py") {
      return (
        <svg
          viewBox="0 0 256 255"
          width="16"
          height="16"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient
              x1="12.959%"
              y1="12.039%"
              x2="79.639%"
              y2="78.201%"
              id="a"
            >
              <stop stopColor="#387EB8" offset="0%" />
              <stop stopColor="#366994" offset="100%" />
            </linearGradient>
            <linearGradient
              x1="19.128%"
              y1="20.579%"
              x2="90.742%"
              y2="88.429%"
              id="b"
            >
              <stop stopColor="#FFE052" offset="0%" />
              <stop stopColor="#FFC331" offset="100%" />
            </linearGradient>
          </defs>
          <path
            d="M126.916.072c-64.832 0-60.784 28.115-60.784 28.115l.072 29.128h61.868v8.745H41.631S.145 61.355.145 126.77c0 65.417 36.21 63.097 36.21 63.097h21.61v-30.356s-1.165-36.21 35.632-36.21h61.362s34.475.557 34.475-33.319V33.97S194.67.072 126.916.072zM92.802 19.66a11.12 11.12 0 0 1 11.13 11.13 11.12 11.12 0 0 1-11.13 11.13 11.12 11.12 0 0 1-11.13-11.13 11.12 11.12 0 0 1 11.13-11.13z"
            fill="url(#a)"
          />
          <path
            d="M128.757 254.126c64.832 0 60.784-28.115 60.784-28.115l-.072-29.127H127.6v-8.745h86.441s41.486 4.705 41.486-60.712c0-65.416-36.21-63.096-36.21-63.096h-21.61v30.355s1.165 36.21-35.632 36.21h-61.362s-34.475-.557-34.475 33.32v56.013s-5.235 33.897 62.518 33.897zm34.114-19.586a11.12 11.12 0 0 1-11.13-11.13 11.12 11.12 0 0 1 11.13-11.131 11.12 11.12 0 0 1 11.13 11.13 11.12 11.12 0 0 1-11.13 11.13z"
            fill="url(#b)"
          />
        </svg>
      );
    } else if (
      language === "jsx" ||
      language === "tsx" ||
      language === "react"
    ) {
      return (
        <svg
          height="16"
          style={{ shapeRendering: "auto" }}
          viewBox="-11.5 -10.23174 23 20.46348"
          width="16"
        >
          <circle cx="0" cy="0" fill="currentColor" r="2.05"></circle>
          <g fill="none" stroke="currentColor" strokeWidth="1">
            <ellipse rx="11" ry="4.2"></ellipse>
            <ellipse rx="11" ry="4.2" transform="rotate(60)"></ellipse>
            <ellipse rx="11" ry="4.2" transform="rotate(120)"></ellipse>
          </g>
        </svg>
      );
    } else if (language === "javascript" || language === "js") {
      return (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
        >
          <path
            fill="#F7DF1E"
            d="M0 0h24v24H0V0zm22.034 18.276c-.175-1.095-.888-2.015-3.003-2.873-.736-.345-1.554-.585-1.797-1.14-.091-.33-.105-.51-.046-.705.15-.646.915-.84 1.515-.66.39.12.75.42.976.9 1.034-.676 1.034-.676 1.755-1.125-.27-.42-.404-.601-.586-.78-.63-.705-1.469-1.065-2.834-1.034l-.705.089c-.676.165-1.32.525-1.71 1.005-1.14 1.291-.811 3.541.569 4.471 1.365 1.02 3.361 1.244 3.616 2.205.24 1.17-.87 1.545-1.966 1.41-.811-.18-1.26-.586-1.755-1.336l-1.83 1.051c.21.48.45.689.81 1.109 1.74 1.756 6.09 1.666 6.871-1.004.029-.09.24-.705.074-1.65l.046.067zm-8.983-7.245h-2.248c0 1.938-.009 3.864-.009 5.805 0 1.232.063 2.363-.138 2.711-.33.689-1.18.601-1.566.48-.396-.196-.597-.466-.83-.855-.063-.105-.11-.196-.127-.196l-1.825 1.125c.305.63.75 1.172 1.324 1.517.855.51 2.004.675 3.207.405.783-.226 1.458-.691 1.811-1.411.51-.93.402-2.07.396-3.346.012-2.054 0-4.109 0-6.179l.004-.056z"
          />
        </svg>
      );
    } else if (language === "typescript" || language === "ts") {
      return (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
        >
          <path
            fill="#3178C6"
            d="M1.125 0C.502 0 0 .502 0 1.125v21.75C0 23.498.502 24 1.125 24h21.75c.623 0 1.125-.502 1.125-1.125V1.125C24 .502 23.498 0 22.875 0H1.125zm17.363 9.75c.612 0 1.154.037 1.627.111a6.38 6.38 0 0 1 1.306.34v2.458a3.95 3.95 0 0 0-.643-.361 5.093 5.093 0 0 0-.717-.26 5.453 5.453 0 0 0-1.426-.2c-.3 0-.573.028-.819.086a2.1 2.1 0 0 0-.623.242c-.17.104-.3.229-.393.374a.888.888 0 0 0-.14.49c0 .196.053.373.156.529.104.156.252.304.443.444s.423.276.696.41c.273.135.582.274.926.416.47.197.892.407 1.266.628.374.222.695.473.963.753.268.279.472.598.614.957.142.359.214.776.214 1.253 0 .657-.125 1.21-.374 1.656a3.033 3.033 0 0 1-1.012 1.085 4.38 4.38 0 0 1-1.487.596c-.566.12-1.163.18-1.79.18a9.916 9.916 0 0 1-1.84-.164 5.544 5.544 0 0 1-1.512-.493v-2.63a5.033 5.033 0 0 0 3.237 1.2c.333 0 .624-.03.872-.09.249-.06.456-.144.623-.25.166-.108.29-.234.373-.38a1.023 1.023 0 0 0-.074-1.089 2.12 2.12 0 0 0-.537-.5 5.597 5.597 0 0 0-.807-.444 27.72 27.72 0 0 0-1.007-.436c-.918-.383-1.602-.852-2.053-1.405-.45-.553-.676-1.222-.676-2.005 0-.614.123-1.141.369-1.582.246-.441.58-.804 1.004-1.089a4.494 4.494 0 0 1 1.47-.629 7.536 7.536 0 0 1 1.77-.201zm-15.113.188h9.563v2.166H9.506v9.646H6.789v-9.646H3.375V9.938z"
          />
        </svg>
      );
    } else if (language === "html") {
      return (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
        >
          <path
            fill="#E34F26"
            d="M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.23-2.622L5.412 4.41l.698 8.01h9.126l-.326 3.426-2.91.804-2.955-.81-.188-2.11H6.248l.33 4.171L12 19.351l5.379-1.443.744-8.157H8.531z"
          />
        </svg>
      );
    } else if (language === "css") {
      return (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
        >
          <path
            fill="#1572B6"
            d="M1.5 0h21l-1.91 21.563L11.977 24l-8.565-2.438L1.5 0zm17.09 4.413L5.41 4.41l.213 2.622 10.125.002-.255 2.716h-6.64l.24 2.573h6.182l-.366 3.523-2.91.804-2.956-.81-.188-2.11h-2.61l.29 3.855L12 19.288l5.373-1.53L18.59 4.414v-.001z"
          />
        </svg>
      );
    } else {
      // Default - document icon
      return (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
      );
    }
  };

  // Custom Geist-inspired theme
  const geistTheme = {
    'code[class*="language-"]': {
      color: "#000",
      background: "transparent",
      fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
      fontSize: currentFontSize,
      textAlign: "left",
      whiteSpace: "pre",
      wordSpacing: "normal",
      wordBreak: "normal",
      wordWrap: "normal",
      lineHeight: "1.5",
      tabSize: 2,
      hyphens: "none",
    },
    'pre[class*="language-"]': {
      color: "#000",
      background: "white",
      fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
      fontSize: currentFontSize,
      textAlign: "left",
      whiteSpace: "pre",
      wordSpacing: "normal",
      wordBreak: "normal",
      wordWrap: "normal",
      lineHeight: "1.5",
      tabSize: 2,
      hyphens: "none",
      padding: "1rem",
      margin: "0",
      overflow: "auto",
      borderRadius: filename ? "0 0 0.375rem 0.375rem" : "0.375rem",
    },
    comment: {
      color: "#6e7781",
      fontStyle: "italic",
    },
    punctuation: {
      color: "#24292f",
    },
    property: {
      color: "#0550ae",
    },
    tag: {
      color: "#116329",
    },
    boolean: {
      color: "#0550ae",
    },
    number: {
      color: "#0550ae",
    },
    constant: {
      color: "#0550ae",
    },
    symbol: {
      color: "#0550ae",
    },
    selector: {
      color: "#116329",
    },
    "attr-name": {
      color: "#953800",
    },
    string: {
      color: "#0a3069",
    },
    char: {
      color: "#0a3069",
    },
    builtin: {
      color: "#cf222e",
    },
    operator: {
      color: "#cf222e",
    },
    entity: {
      color: "#116329",
      cursor: "help",
    },
    url: {
      color: "#0550ae",
    },
    "attr-value": {
      color: "#0a3069",
    },
    keyword: {
      color: "#cf222e",
    },
    regex: {
      color: "#116329",
    },
    important: {
      color: "#953800",
      fontWeight: "bold",
    },
    variable: {
      color: "#953800",
    },
    bold: {
      fontWeight: "bold",
    },
    italic: {
      fontStyle: "italic",
    },
    inserted: {
      color: "#116329",
      backgroundColor: "#dafbe1",
    },
    deleted: {
      color: "#82071e",
      backgroundColor: "#ffebe9",
    },
    ".line": {
      display: "block",
      width: "100%",
    },
    ".line-highlight": {
      backgroundColor: "rgba(245, 228, 0, 0.2)",
      width: "100%",
      display: "block",
      borderLeft: "2px solid rgb(245, 228, 0)",
      marginLeft: "-1rem",
      paddingLeft: "calc(1rem - 2px)",
    },
  };

  // Function to apply line highlighting
  const lineProps = (lineNumber) => {
    const isHighlighted = highlightLines.includes(lineNumber);

    return {
      className: isHighlighted
        ? "bg-[#00800026] -ml-4 pl-4 min-w-[calc(100%_+_2rem)]"
        : "",
      style: {
        display: "block",
        width: "100%",
      },
    };
  };

  return (
    <div className="overflow-hidden rounded-lg font-mono border border-gray-200">
      {filename && (
        <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b">
          <div className="flex items-center">
            <div className="mr-4">{getLanguageIcon()}</div>
            <span className="text-xs sm:text-sm font-normal text-gray-700">
              {filename}
            </span>
          </div>
          <div>
            <button
              aria-label="Copy code"
              className="cursor-pointer p-1 font-normal text-gray-500 flex items-center justify-center"
              type="button"
              onClick={handleCopy}
            >
              {!copied ? <Copy size="20" /> : <Check size="20" />}
            </button>
          </div>
        </div>
      )}
      <SyntaxHighlighter
        language={language}
        style={geistTheme}
        showLineNumbers={showLineNumbers}
        wrapLines={true}
        lineProps={lineProps}
        customStyle={{
          margin: 0,
          padding: "1rem",
          background: "white",
          borderRadius: "0 0 0.375rem 0.375rem",
        }}
        lineNumberStyle={{
          minWidth: "2.5em",
          paddingRight: "1.5em",
          textAlign: "right",
          color: "rgba(115, 138, 148, 0.6)",
          userSelect: "none",
          fontStyle: "normal", // Remove italics
          fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
        }}
        codeTagProps={{
          className: "font-mono",
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
};
