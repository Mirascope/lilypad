import JSON5 from "json5";

export const stringToBytes = (data: string): Uint8Array => {
  const binaryString = window.atob(data);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
};

interface FormattedTextProps {
  template: string;
  values?: Record<string, string>;
}

export const FormattedText = ({
  template,
  values = {},
}: FormattedTextProps) => {
  const parts = template.split(/(\{[^}]+\})/g);

  return (
    <p>
      {parts.map((part, index) => {
        const match = /\{([^}]+)\}/.exec(part);
        if (match) {
          const key = match[1];
          return (
            <span
              key={index}
              className={key in values ? "text-purple-500" : undefined}
            >
              {part}
            </span>
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </p>
  );
};

export const safelyParseJSON = (json: string): object | undefined => {
  let parsed = undefined;

  try {
    parsed = JSON5.parse(json);
  } catch (e) {}

  return parsed;
};
export const formatDate = (utcDateString?: string, dateOnly = true): string => {
  if (!utcDateString) {
    return "";
  }
  const date = new Date(utcDateString);
  return new Intl.DateTimeFormat(navigator.language, {
    year: "numeric",
    month: "2-digit",
    day: "numeric",
    ...(dateOnly && {
      hour: "numeric",
      minute: "numeric",
      second: "numeric",
      hour12: true,
    }),
    timeZoneName: "short",
  }).format(date);
};
