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
import { cn } from "@/lib/utils";
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
  dialogContentProps = {},
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
  dialogContentProps?: React.ComponentProps<typeof DialogContent>;
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
          <TooltipTrigger asChild>
            {<span>{TriggerButton}</span>}
          </TooltipTrigger>
          <TooltipContent {...tooltipProps}>{tooltipContent}</TooltipContent>
        </Tooltip>
      ) : (
        TriggerButton
      )}
      <DialogContent
        className={cn(
          "max-w-[425px] overflow-x-auto",
          dialogContentProps?.className
        )}
        {...dialogContentProps}
      >
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
