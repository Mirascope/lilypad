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
  values?: {
    [key: string]: string;
  };
}

export const FormattedText: React.FC<FormattedTextProps> = ({
  template,
  values = {},
}) => {
  const parts = template.split(/(\{[^}]+\})/g);

  return (
    <p>
      {parts.map((part, index) => {
        const match = part.match(/\{([^}]+)\}/);
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
    parsed = JSON.parse(json);
  } catch (e) {}

  return parsed;
};
export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat(navigator.language, {
    year: "numeric",
    month: "2-digit",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    hour12: true,
    timeZoneName: "short",
  }).format(date);
};
