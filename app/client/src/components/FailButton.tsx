import { Button, ButtonProps } from "@/src/components/ui/button";
import { XCircle } from "lucide-react";

export const FailButton = ({ children, ...buttonProps }: ButtonProps) => {
  return (
    <Button type="button" variant="destructive" {...buttonProps}>
      <XCircle className="mr-2 h-4 w-4" />
      {children}
    </Button>
  );
};
