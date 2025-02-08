import { Button, ButtonProps } from "@/components/ui/button";
import { CheckCircle } from "lucide-react";

export const SuccessButton = ({ children, ...buttonProps }: ButtonProps) => {
  return (
    <Button type='button' variant='success' {...buttonProps}>
      <CheckCircle className='w-4 h-4 mr-2' />
      {children}
    </Button>
  );
};
