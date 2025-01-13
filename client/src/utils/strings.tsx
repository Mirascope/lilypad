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
