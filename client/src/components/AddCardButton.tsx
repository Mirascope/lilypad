import React from "react";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface AddCardButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  className?: string;
  onClick?: () => void;
}

export const AddCardButton: React.FC<AddCardButtonProps> = ({
  className,
  onClick,
  ...props
}) => {
  return (
    <Button
      type="button"
      onClick={onClick}
      className={cn(
        "w-64 h-[216px] shrink-0 border-2 border-dashed rounded-lg border-gray-200 hover:border-gray-300 transition-colors flex items-center justify-center bg-transparent hover:bg-slate-50",
        className
      )}
      {...props}
    >
      <Plus className="h-6 w-6 text-gray-400" />
    </Button>
  );
};
