import { Button, ButtonProps } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ReactNode } from "react";

export const IconDialog = ({
  icon,
  text,
  title,
  description,
  children,
  buttonProps = {},
  tooltipContent,
  tooltipProps = {},
  dialogButtons,
  onOpenChange,
}: {
  icon?: ReactNode;
  text?: string;
  title: string;
  description: string;
  children: ReactNode;
  buttonProps?: ButtonProps;
  tooltipContent?: ReactNode;
  tooltipProps?: React.ComponentProps<typeof TooltipContent>;
  dialogButtons?: ReactNode[];
  onOpenChange?: (open: boolean) => void;
}) => {
  const ButtonComponent = (
    <Button
      variant='outline'
      {...buttonProps}
      size={icon ? "icon" : buttonProps.size}
    >
      {icon || text}
    </Button>
  );

  const TriggerButton = (
    <DialogTrigger asChild>{ButtonComponent}</DialogTrigger>
  );

  return (
    <Dialog onOpenChange={onOpenChange}>
      {tooltipContent ? (
        <Tooltip>
          <TooltipTrigger asChild>{TriggerButton}</TooltipTrigger>
          <TooltipContent {...tooltipProps}>{tooltipContent}</TooltipContent>
        </Tooltip>
      ) : (
        TriggerButton
      )}
      <DialogContent className='max-w-[425px]'>
        <DialogHeader className='flex-shrink-0'>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div>{children}</div>
        <DialogFooter>
          {dialogButtons?.map((button, i) => (
            <DialogClose key={i} asChild>
              {button}
            </DialogClose>
          ))}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default IconDialog;
