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

export const FormattedText = ({ template, values = {} }: FormattedTextProps) => {
  const parts = template.split(/(\{[^}]+\})/g);

  return (
    <p>
      {parts.map((part, index) => {
        const match = /\{([^}]+)\}/.exec(part);
        if (match) {
          const key = match[1];
          return (
            <span key={index} className={key in values ? "text-purple-500" : undefined}>
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
export const formatDate = (utcDateString?: string | number | Date, dateOnly = true): string => {
  if (!utcDateString) {
    return "";
  }
  let date;
  // Convert to Date object if it's a string
  if (typeof utcDateString === "string" || typeof utcDateString === "number") {
    date = new Date(utcDateString);
  } else {
    date = utcDateString;
  }
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

export const formatRelativeTime = (
  utcDateString?: string | number | Date,
  shorthand = false
): string => {
  if (!utcDateString) {
    return "";
  }

  let date;
  // Convert to Date object if it's a string
  if (typeof utcDateString === "string" || typeof utcDateString === "number") {
    date = new Date(utcDateString);
  } else {
    date = utcDateString;
  }
  const now = new Date();

  // Time difference in milliseconds
  const diffMs = now.getTime() - date.getTime();

  // Convert to different time units
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30); // Approximate

  // Choose appropriate unit
  if (diffMinutes < 60) {
    return shorthand
      ? `${diffMinutes}m`
      : `${diffMinutes} ${diffMinutes === 1 ? "minute" : "minutes"} ago`;
  } else if (diffHours < 24) {
    return shorthand ? `${diffHours}h` : `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  } else if (diffDays < 7) {
    return shorthand ? `${diffDays}d` : `${diffDays} ${diffDays === 1 ? "day" : "days"} ago`;
  } else if (diffWeeks < 5) {
    return shorthand ? `${diffWeeks}w` : `${diffWeeks} ${diffWeeks === 1 ? "week" : "weeks"} ago`;
  } else {
    return shorthand
      ? `${diffMonths}mo`
      : `${diffMonths} ${diffMonths === 1 ? "month" : "months"} ago`;
  }
};
