import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export const CopyButton = ({ content }: { content: string }) => {
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const copyToClipboard = () => {
    navigator.clipboard.writeText(content);
    setIsCopied(true);
    toast.success("Successfully copied to clipboard");
    setTimeout(() => setIsCopied(false), 2000);
  };
  return (
    <button
      className="relative cursor-pointer rounded-md border bg-background p-1.5 hover:bg-muted"
      onClick={copyToClipboard}
      aria-label="Copy code"
      title="Copy code"
    >
      {isCopied ? <Check className="size-4" /> : <Copy className="size-4" />}
    </button>
  );
};
