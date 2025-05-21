import { Button, ButtonProps } from "@/components/ui/button";
import { CheckCircle } from "lucide-react";

export const SuccessButton = ({ children, ...buttonProps }: ButtonProps) => {
  return (
    <Button type="button" {...buttonProps}>
      <CheckCircle className="mr-2 h-4 w-4" />
      {children}
    </Button>
  );
};
