import { Button } from "@/src/components/ui/button";
import { cn } from "@/src/lib/utils";
import { Plus } from "lucide-react";
import React from "react";

interface AddCardButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  className?: string;
  onClick?: () => void;
}

export const AddCardButton: React.FC<AddCardButtonProps> = ({ className, onClick, ...props }) => {
  return (
    <Button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-[216px] w-64 shrink-0 items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-transparent transition-colors hover:border-gray-300 hover:bg-slate-50",
        className
      )}
      {...props}
    >
      <Plus className="h-6 w-6 text-gray-400" />
    </Button>
  );
};
