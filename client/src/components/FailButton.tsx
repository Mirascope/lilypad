import { Button, ButtonProps } from "@/components/ui/button";
import { XCircle } from "lucide-react";

export const FailButton = ({ children, ...buttonProps }: ButtonProps) => {
  return (
    <Button type='button' variant='destructive' {...buttonProps}>
      <XCircle className='w-4 h-4 mr-2' />
      {children}
    </Button>
  );
};
